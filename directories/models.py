from django.db import models
from django.utils import timezone
from django.urls import reverse
from .utils import delete_image_and_thumbnail

class SoftDeleteManager(models.Manager):
    """Менеджер, исключающий удалённые объекты"""
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

class Directory(models.Model):
    name = models.CharField('Название', max_length=100)
    slug = models.SlugField('Системное имя', max_length=100, unique=True)
    description = models.TextField('Описание', blank=True)
    is_deleted = models.BooleanField('Удалён', default=False)
    deleted_at = models.DateTimeField('Дата удаления', null=True, blank=True)
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        verbose_name = 'Справочник'
        verbose_name_plural = 'Справочники'
        ordering = ['name']
        permissions = [
            ('can_soft_delete_directory', 'Может мягко удалять справочник'),
            ('can_hard_delete_directory', 'Может полностью удалять справочник'),
            ('can_restore_directory', 'Может восстанавливать справочник'),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('directories:directory_list')

    def soft_delete(self):
        if not self.is_deleted:
            self.is_deleted = True
            self.deleted_at = timezone.now()
            self.save()
            # Каскадное мягкое удаление полей и записей
            for field in self.fields.all():
                field.soft_delete()
            for record in self.records.all():
                record.soft_delete()

    def restore(self):
        if self.is_deleted:
            self.is_deleted = False
            self.deleted_at = None
            self.save()
            # Восстанавливать поля и записи не автоматически — администратор решит сам

    def hard_delete(self):
        # Удаляем все записи (их hard_delete удалит файлы)
        for record in self.records.all():
            record.hard_delete()
        # Удаляем все поля (их hard_delete удалит связанные значения и файлы)
        for field in self.fields.all():
            field.hard_delete()
        # Удаляем сам справочник
        self.delete()

class Field(models.Model):
    FIELD_TYPES = [
        ('text', 'Текст'),
        ('number', 'Число'),
        ('date', 'Дата'),
        ('boolean', 'Да/Нет'),
        ('reference', 'Ссылка на другой справочник'),
        ('image', 'Изображение'),
    ]
    directory = models.ForeignKey(Directory, on_delete=models.CASCADE, related_name='fields', verbose_name='Справочник')
    name = models.CharField('Название поля', max_length=100)
    description = models.CharField('Описание', max_length=200, blank=True)
    field_type = models.CharField('Тип поля', max_length=20, choices=FIELD_TYPES, default='text')
    reference_directory = models.ForeignKey(Directory, on_delete=models.SET_NULL, null=True, blank=True,
                                            related_name='referencing_fields', verbose_name='Справочник-источник')
    is_required = models.BooleanField('Обязательное', default=False)
    position = models.PositiveIntegerField('Позиция', default=0)
    # Для типа image
    thumb_width = models.PositiveIntegerField('Ширина миниатюры', null=True, blank=True, default=100)
    thumb_height = models.PositiveIntegerField('Высота миниатюры', null=True, blank=True, default=100)
    max_size_mb = models.PositiveIntegerField('Макс. размер (Мб)', default=1)

    is_deleted = models.BooleanField('Удалено', default=False)
    deleted_at = models.DateTimeField('Дата удаления', null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        verbose_name = 'Поле справочника'
        verbose_name_plural = 'Поля справочников'
        ordering = ['directory', 'position', 'name']
        permissions = [
            ('can_soft_delete_field', 'Может мягко удалять поле'),
            ('can_hard_delete_field', 'Может полностью удалять поле'),
            ('can_restore_field', 'Может восстанавливать поле'),
        ]

    def __str__(self):
        return f"{self.directory.name} → {self.name}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.field_type == 'reference' and not self.reference_directory:
            raise ValidationError({'reference_directory': 'Для типа "Ссылка" выберите справочник-источник.'})
        if self.field_type != 'image':
            self.thumb_width = None
            self.thumb_height = None
        # Уникальность имени поля среди активных полей того же справочника
        if not self.is_deleted:
            qs = Field.objects.filter(directory=self.directory, name=self.name, is_deleted=False)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError({'name': 'Поле с таким именем уже существует в этом справочнике.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def soft_delete(self):
        if not self.is_deleted:
            self.is_deleted = True
            self.deleted_at = timezone.now()
            self.save()
            # Мягкое удаление значений (RecordValue) этого поля
            self.values.update(is_deleted=True, deleted_at=timezone.now())

    def restore(self):
        if self.is_deleted:
            self.is_deleted = False
            self.deleted_at = None
            self.save()
            self.values.update(is_deleted=False, deleted_at=None)

    def hard_delete(self):
        # Удаляем все значения этого поля (они удалят файлы для image)
        for value in self.values.all():
            value.hard_delete()
        self.delete()

class Record(models.Model):
    directory = models.ForeignKey(Directory, on_delete=models.CASCADE, related_name='records', verbose_name='Справочник')
    is_deleted = models.BooleanField('Удалена', default=False)
    deleted_at = models.DateTimeField('Дата удаления', null=True, blank=True)
    created_at = models.DateTimeField('Создана', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлена', auto_now=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        verbose_name = 'Запись справочника'
        verbose_name_plural = 'Записи справочников'
        ordering = ['-created_at']
        permissions = [
            ('can_soft_delete_record', 'Может мягко удалять запись'),
            ('can_hard_delete_record', 'Может полностью удалять запись'),
            ('can_restore_record', 'Может восстанавливать запись'),
        ]

    def __str__(self):
        # Пытаемся отобразить первое текстовое значение
        text_value = self.values.filter(field__field_type='text', is_deleted=False).first()
        if text_value and text_value.value:
            return f"{self.directory.name}: {text_value.value}"
        return f"{self.directory.name}: Запись #{self.id}"

    def get_absolute_url(self):
        return reverse('directories:record_detail', args=[self.directory.slug, self.pk])

    def soft_delete(self):
        if not self.is_deleted:
            self.is_deleted = True
            self.deleted_at = timezone.now()
            self.save()
            self.values.update(is_deleted=True, deleted_at=timezone.now())

    def restore(self):
        if self.is_deleted:
            self.is_deleted = False
            self.deleted_at = None
            self.save()
            self.values.update(is_deleted=False, deleted_at=None)

    def hard_delete(self):
        # Удаляем значения (с файлами)
        for value in self.values.all():
            value.hard_delete()
        self.delete()

class RecordValue(models.Model):
    record = models.ForeignKey(Record, on_delete=models.CASCADE, related_name='values', verbose_name='Запись')
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='values', verbose_name='Поле')
    value = models.TextField('Значение', blank=True)
    is_deleted = models.BooleanField('Удалено', default=False)
    deleted_at = models.DateTimeField('Дата удаления', null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        verbose_name = 'Значение поля'
        verbose_name_plural = 'Значения полей'
        unique_together = [['record', 'field']]

    def __str__(self):
        return f"{self.record} → {self.field.name}: {self.value[:50]}"

    def soft_delete(self):
        if not self.is_deleted:
            self.is_deleted = True
            self.deleted_at = timezone.now()
            self.save()

    def restore(self):
        if self.is_deleted:
            self.is_deleted = False
            self.deleted_at = None
            self.save()

    def hard_delete(self):
        if self.field.field_type == 'image' and self.value:
            delete_image_and_thumbnail(self.value)
        self.delete()