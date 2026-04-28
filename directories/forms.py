from django import forms
from django.core.exceptions import ValidationError
from .models import Directory, Field, Record, RecordValue
from .utils import save_image_with_thumbnail, delete_image_and_thumbnail

class DirectoryForm(forms.ModelForm):
    class Meta:
        model = Directory
        fields = ('name', 'slug', 'description')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'slug': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 4}),
        }

    def clean_slug(self):
        slug = self.cleaned_data['slug']
        # Уникальность среди всех справочников (включая удалённые) – обеспечивается unique=True в модели
        return slug

class FieldForm(forms.ModelForm):
    class Meta:
        model = Field
        fields = ('name', 'description', 'field_type', 'reference_directory',
                  'is_required', 'position', 'thumb_width', 'thumb_height', 'max_size_mb')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
            'field_type': forms.Select(attrs={'class': 'form-input'}),
            'reference_directory': forms.Select(attrs={'class': 'form-input'}),
            'is_required': forms.CheckboxInput(attrs={'class': 'form-input', 'style': 'width: auto;'}),
            'position': forms.NumberInput(attrs={'class': 'form-input'}),
            'thumb_width': forms.NumberInput(attrs={'class': 'form-input'}),
            'thumb_height': forms.NumberInput(attrs={'class': 'form-input'}),
            'max_size_mb': forms.NumberInput(attrs={'class': 'form-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        field_type = cleaned_data.get('field_type')
        if field_type == 'reference' and not cleaned_data.get('reference_directory'):
            self.add_error('reference_directory', 'Для типа "Ссылка" выберите справочник-источник.')
        if field_type != 'image':
            cleaned_data['thumb_width'] = None
            cleaned_data['thumb_height'] = None
        return cleaned_data

class RecordForm(forms.ModelForm):
    """Динамическая форма для записей, поля генерируются на основе Field"""
    class Meta:
        model = Record
        fields = ()

    def __init__(self, directory, *args, **kwargs):
        self.directory = directory
        super().__init__(*args, **kwargs)
        self.fields_dict = {}
        fields = directory.fields.filter(is_deleted=False)
        for field in fields:
            field_name = f"field_{field.id}"
            self.fields_dict[field.id] = field

            # Определяем виджет и тип поля
            if field.field_type == 'text':
                self.fields[field_name] = forms.CharField(
                    required=field.is_required,
                    widget=forms.TextInput(attrs={'class': 'form-input'}),
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
            # Заполняем начальные значения, если запись уже существует
            if self.instance.pk:
                existing = RecordValue.objects.filter(record=self.instance, field=field).first()
                if existing:
                    val = existing.value
                    if field.field_type == 'boolean':
                        val = val == 'True'
                    elif field.field_type == 'reference':
                        val = val if val else ''
                    elif field.field_type == 'image':
                        # Для изображений не подставляем начальное значение в input, а показываем отдельный блок в шаблоне
                        self.initial[field_name] = None
                        # Сохраняем текущий путь для возможного удаления старого файла
                        self._current_image_path = val
                        continue
                    self.initial[field_name] = val

    def clean(self):
        cleaned_data = super().clean()
        # Дополнительная валидация для изображений (размер, формат)
        for field_id, field in self.fields_dict.items():
            if field.field_type == 'image':
                uploaded_file = cleaned_data.get(f"field_{field_id}")
                if uploaded_file:
                    # Проверка размера и расширения будет выполнена в save_image_with_thumbnail, но можем и здесь
                    if uploaded_file.size > field.max_size_mb * 1024 * 1024:
                        self.add_error(f"field_{field_id}", f"Файл слишком большой (максимум {field.max_size_mb} Мб)")
        return cleaned_data

    def save(self, commit=True):
        record = super().save(commit=False)
        if commit:
            record.save()
            # Удаляем старые значения, которые не были переданы (но лучше обновить/создать)
            for field_id, field in self.fields_dict.items():
                field_name = f"field_{field_id}"
                raw_value = self.cleaned_data.get(field_name)
                # Преобразование значения в строку для хранения
                if field.field_type == 'boolean':
                    str_value = 'True' if raw_value else 'False'
                elif field.field_type == 'date' and raw_value:
                    str_value = raw_value.isoformat()
                elif field.field_type == 'reference':
                    str_value = str(raw_value) if raw_value else ''
                elif field.field_type == 'image':
                    uploaded_file = raw_value
                    if uploaded_file:
                        # Удаляем старый файл, если он существует
                        old_value = RecordValue.objects.filter(record=record, field=field).first()
                        if old_value and old_value.value:
                            delete_image_and_thumbnail(old_value.value)
                        # Сохраняем новое изображение
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
                            # Ошибка валидации – добавим к форме, но здесь просто пропустим? Лучше поднять ValidationError
                            raise forms.ValidationError(f"Ошибка изображения: {e}")
                    else:
                        # Если файл не загружен и поле обязательное – ошибка будет выше
                        continue
                else:
                    str_value = str(raw_value) if raw_value is not None else ''
                RecordValue.objects.update_or_create(
                    record=record,
                    field=field,
                    defaults={'value': str_value, 'is_deleted': False, 'deleted_at': None}
                )
        return record