# core/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify

class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

class BaseAlbum(models.Model):
    title = models.CharField('Название', max_length=200)
    description = models.TextField('Описание', blank=True)
    author = models.CharField('Автор', max_length=200, blank=True)
    source = models.URLField('Источник', blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Владелец',
                              related_name='%(class)s_albums')
    privacy = models.CharField('Приватность', max_length=20,
                               choices=[('public', 'Публичный'),
                                        ('by_link', 'По ссылке'),
                                        ('private', 'Только владелец')],
                               default='public')
    cover = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Обложка', related_name='+')
    order = models.PositiveIntegerField('Порядок', default=0)
    view_count = models.PositiveIntegerField('Просмотры', default=0)
    slug = models.SlugField('Slug', max_length=200, unique=True, blank=True)
    is_deleted = models.BooleanField('Удалён', default=False)
    deleted_at = models.DateTimeField('Дата удаления', null=True, blank=True)
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True
        ordering = ['-order', '-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            import uuid
            self.slug = uuid.uuid4().hex[:12]  # уникальная строка
        super().save(*args, **kwargs)

    def hard_delete(self):
        # У альбома нет своих файлов, просто удаляем запись
        self.delete()

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

    def get_absolute_url(self):
        from django.urls import reverse
        return '#'

    def has_access(self, user):
        if user.is_superuser or user.is_staff:
            return True
        if self.owner == user:
            return True
        if self.privacy == 'public':
            return True
        if self.privacy == 'by_link' and user.is_authenticated:
            return True
        return False


class BaseMediaItem(models.Model):
    original_name = models.CharField('Исходное имя файла', max_length=255, blank=True)  # теперь необязательное
    file_original = models.FileField('Файл (оригинал)', upload_to='', blank=True, null=True)
    file_optimized = models.FileField('Файл (оптимизированный)', upload_to='', blank=True, null=True)
    file_thumbnail = models.FileField('Файл (превью)', upload_to='', blank=True, null=True)
    position = models.PositiveIntegerField('Позиция', default=0)
    uploaded_at = models.DateTimeField('Дата загрузки', auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    verbose_name='Загрузил', related_name='uploaded_media')
    mime_type = models.CharField('MIME-тип', max_length=100, blank=True)
    metadata = models.JSONField('Метаданные', default=dict, blank=True)
    is_deleted = models.BooleanField('Удалён', default=False)
    deleted_at = models.DateTimeField('Дата удаления', null=True, blank=True)

    author = models.CharField('Автор (элемента)', max_length=200, blank=True)
    source = models.URLField('Источник (элемента)', blank=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True
        ordering = ['position', 'uploaded_at']

    def __str__(self):
        return self.original_name or f"Media #{self.pk}"

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
        from django.core.files.storage import default_storage
        for field in ['file_original', 'file_optimized', 'file_thumbnail']:
            f = getattr(self, field)
            if f and default_storage.exists(f.name):
                default_storage.delete(f.name)
        self.delete()

    def save(self, *args, **kwargs):
        if hasattr(self, 'album') and self.album:
            if not self.author:
                self.author = self.album.author
            if not self.source:
                self.source = self.album.source
        super().save(*args, **kwargs)

    def get_original_url(self):
        return self.file_original.url if self.file_original else ''

    def get_optimized_url(self):
        return self.file_optimized.url if self.file_optimized else ''

    def get_thumbnail_url(self):
        return self.file_thumbnail.url if self.file_thumbnail else ''