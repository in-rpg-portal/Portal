from django import forms
from django.core.exceptions import ValidationError
from django_ckeditor_5.widgets import CKEditor5Widget
from .models import Directory, Field, Record, RecordValue
from .utils import save_image_with_thumbnail, delete_image_and_thumbnail

class DirectoryForm(forms.ModelForm):
    class Meta:
        model = Directory
        fields = ('name', 'slug', 'description')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'slug': forms.TextInput(attrs={'class': 'form-input'}),
            #'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 4}), #Стандартная форма для поля TextArea
            #'description': CKEditor5Widget(config_name='default', attrs={'class': 'form-input'}),
            'description': CKEditor5Widget(config_name='default', attrs={'class': 'form-input django_ckeditor_5'}),
        }

    def clean_slug(self):
        slug = self.cleaned_data['slug']
        # уникальность проверяется в модели
        return slug


class FieldForm(forms.ModelForm):
    # Явное объявление поля max_length
    max_length = forms.IntegerField(
        required=False,
        label='Максимальная длина',
        widget=forms.NumberInput(attrs={'class': 'form-input'})
    )

    class Meta:
        model = Field
        fields = ('name', 'description', 'field_type', 'reference_directory',
                  'is_required', 'position', 'thumb_width', 'thumb_height', 'max_size_mb')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            #'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),  #Стандартная форма для поля TextArea
            #'description': CKEditor5Widget(config_name='default', attrs={'class': 'form-input'}),
            'description': CKEditor5Widget(config_name='default', attrs={'class': 'form-input django_ckeditor_5'}),
            'field_type': forms.Select(attrs={'class': 'form-input'}),
            'reference_directory': forms.Select(attrs={'class': 'form-input'}),
            'is_required': forms.CheckboxInput(attrs={'class': 'form-input', 'style': 'width: auto;'}),
            'position': forms.NumberInput(attrs={'class': 'form-input'}),
            'thumb_width': forms.NumberInput(attrs={'class': 'form-input'}),
            'thumb_height': forms.NumberInput(attrs={'class': 'form-input'}),
            'max_size_mb': forms.NumberInput(attrs={'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.initial['max_length'] = self.instance.max_length

    def clean(self):
        cleaned_data = super().clean()
        field_type = cleaned_data.get('field_type')

        # Валидация для типа reference
        if field_type == 'reference' and not cleaned_data.get('reference_directory'):
            self.add_error('reference_directory', 'Для типа "Ссылка" выберите справочник-источник.')

        # Очистка полей для типов, отличных от image
        if field_type != 'image':
            cleaned_data['thumb_width'] = None
            cleaned_data['thumb_height'] = None

        # Обработка max_length: берём значение напрямую из self.data (сырых POST-данных)
        if field_type == 'string':
            raw_max_length = self.data.get('max_length')
            if raw_max_length is None or raw_max_length == '':
                self.add_error('max_length', 'Укажите максимальную длину.')
            else:
                try:
                    max_length_val = int(raw_max_length)
                    if max_length_val < 1:
                        self.add_error('max_length', 'Длина должна быть положительным числом.')
                    else:
                        cleaned_data['max_length'] = max_length_val
                except (TypeError, ValueError):
                    self.add_error('max_length', 'Введите целое число.')
        else:
            cleaned_data['max_length'] = None

        # Обновляем значение в экземпляре, если форма валидна
        if hasattr(self, 'instance') and self.instance:
            self.instance.max_length = cleaned_data.get('max_length')

        return cleaned_data


class RecordForm(forms.ModelForm):
    class Meta:
        model = Record
        fields = ()

    def __init__(self, directory, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # получаем текущего пользователя
        self.directory = directory
        super().__init__(*args, **kwargs)
        self.fields_dict = {}
        fields = directory.fields.filter(is_deleted=False)

        for field in fields:
            field_name = f"field_{field.id}"
            self.fields_dict[field.id] = field

            # Тип поля: короткая строка
            if field.field_type == 'string':
                self.fields[field_name] = forms.CharField(
                    required=field.is_required,
                    max_length=field.max_length or 255,
                    widget=forms.TextInput(attrs={'class': 'form-input'}),
                    label=field.name
                )
            # Тип поля: текст (с CKEditor)
            elif field.field_type == 'text':
                self.fields[field_name] = forms.CharField(
                    required=field.is_required,
                    widget=CKEditor5Widget(config_name='default'),
                    label=field.name
                )
            elif field.field_type == 'number':
                self.fields[field_name] = forms.DecimalField(
                    required=field.is_required,
                    widget=forms.NumberInput(attrs={'class': 'form-input'}),
                    label=field.name
                )
            elif field.field_type == 'date':
                self.fields[field_name] = forms.DateField(
                    required=field.is_required,
                    widget=forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
                    label=field.name
                )
            elif field.field_type == 'boolean':
                self.fields[field_name] = forms.BooleanField(
                    required=False,
                    widget=forms.CheckboxInput(attrs={'class': 'form-input', 'style': 'width: auto;'}),
                    label=field.name
                )
            elif field.field_type == 'reference':
                target_dir = field.reference_directory
                choices = [('', '---------')] + [(r.id, str(r)) for r in target_dir.records.filter(is_deleted=False)]
                self.fields[field_name] = forms.ChoiceField(
                    choices=choices,
                    required=field.is_required,
                    widget=forms.Select(attrs={'class': 'form-input'}),
                    label=field.name
                )
            elif field.field_type == 'image':
                self.fields[field_name] = forms.ImageField(
                    required=field.is_required,
                    widget=forms.FileInput(attrs={'class': 'form-input'}),
                    label=field.name,
                    help_text=f"Максимум {field.max_size_mb} Мб. Форматы: jpg, png, gif"
                )

            # Заполнение начальных значений
            if self.instance.pk:
                existing = RecordValue.objects.filter(record=self.instance, field=field).first()
                if existing:
                    val = existing.value
                    if field.field_type == 'boolean':
                        val = val == 'True'
                    elif field.field_type == 'reference':
                        val = val if val else ''
                    elif field.field_type == 'image':
                        self.initial[field_name] = None
                        self._current_image_path = val
                        continue
                    self.initial[field_name] = val

        # Добавляем поле is_default
        self.fields['is_default'] = forms.BooleanField(
            required=False,
            label='Использовать как значение по умолчанию'
        )

        # Настройка disabled для не-админов
        if self.user and not (self.user.is_superuser or self.user.is_staff):
            self.fields['is_default'].widget.attrs['disabled'] = True
            self.fields['is_default'].help_text = 'Только администратор может изменить настройку "по умолчанию".'
        else:
            self.fields['is_default'].widget.attrs['class'] = 'form-input'
            self.fields['position'] = forms.IntegerField(required=False, label='Позиция', widget=forms.NumberInput(attrs={'class': 'form-input'}))
            self.fields['position'].help_text = 'Чем больше число, тем выше запись в списке.'

        if self.instance.pk:
            self.initial['position'] = self.instance.position
        else:
            self.initial['position'] = 0

        # Устанавливаем начальное значение (если запись существует)
        if self.instance.pk:
            self.initial['is_default'] = self.instance.is_default

    def clean(self):
        cleaned_data = super().clean()
        
         # Валидация изображений
        for field_id, field in self.fields_dict.items():
            if field.field_type == 'image':
                uploaded_file = cleaned_data.get(f"field_{field_id}")
                if uploaded_file and uploaded_file.size > field.max_size_mb * 1024 * 1024:
                    self.add_error(f"field_{field_id}", f"Файл слишком большой (максимум {field.max_size_mb} Мб)")
        
        # Проверка уникальности для is_default
        is_default = cleaned_data.get('is_default')
        if is_default and self.instance.pk:
            # Если пользователь не админ, но пытается изменить, то позже восстановим исходное, но здесь просто проверим
            # Для всех, кто пытается установить дефолт, проверяем, нет ли уже другого дефолта
            if Record.objects.filter(directory=self.directory, is_default=True).exclude(pk=self.instance.pk).exists():
                self.add_error('is_default', 'В этом справочнике уже есть запись, отмеченная как значение по умолчанию. Сначала снимите отметку с неё.')
        
        # Защита position: если пользователь не админ, но поле position попытались подменить, игнорируем
        if self.user and not (self.user.is_superuser or self.user.is_staff):
            # Если поле position появилось в cleaned_data (хотя его не должно быть), удаляем
            if 'position' in cleaned_data:
                del cleaned_data['position']
                
        return cleaned_data

    def save(self, commit=True):
        record = super().save(commit=False)

        # Устанавливаем is_default из формы
        record.is_default = self.cleaned_data.get('is_default', False)
        if commit:
            if self.user and (self.user.is_superuser or self.user.is_staff) and 'position' in self.cleaned_data:
                record.position = self.cleaned_data['position']

            record.save()
            # Сохраняем динамические поля
            for field_id, field in self.fields_dict.items():
                field_name = f"field_{field_id}"
                raw_value = self.cleaned_data.get(field_name)

                if field.field_type == 'boolean':
                    str_value = 'True' if raw_value else 'False'
                elif field.field_type == 'date' and raw_value:
                    str_value = raw_value.isoformat()
                elif field.field_type == 'reference':
                    str_value = str(raw_value) if raw_value else ''
                elif field.field_type == 'image':
                    uploaded_file = raw_value
                    if uploaded_file:
                        old_value = RecordValue.objects.filter(record=record, field=field).first()
                        if old_value and old_value.value:
                            delete_image_and_thumbnail(old_value.value)
                        try:
                            relative_path = save_image_with_thumbnail(
                                uploaded_file,
                                record.directory.slug,
                                field.name,
                                field.thumb_width or 100,
                                field.thumb_height or 100,
                                field.max_size_mb
                            )
                            str_value = relative_path
                        except ValueError as e:
                            raise ValidationError(f"Ошибка изображения: {e}")
                    else:
                        continue
                elif field.field_type == 'text':
                    str_value = raw_value if raw_value else ''
                else:
                    str_value = str(raw_value) if raw_value is not None else ''

                RecordValue.objects.update_or_create(
                    record=record,
                    field=field,
                    defaults={'value': str_value, 'is_deleted': False, 'deleted_at': None}
                )
        return record