# photos/models.py

import os
import time
import uuid
import hashlib
import re
from django.db import models
from django.conf import settings
from django.core.files.storage import default_storage
from django.utils import timezone
from PIL import Image
from transliterate import translit

from core.models import BaseAlbum, BaseMediaItem

# Настройки для приложения photos
PHOTO_OPTIMIZED_MAX_WIDTH = 1200     # максимальная ширина оптимизированной версии (в пикселях)
PHOTO_OPTIMIZED_QUALITY = 85         # качество JPEG для оптимизированной версии (1-100)
PHOTO_THUMBNAIL_SIZE = (200, 200)    # размер превью (ширина, высота) в пикселях

# ------------------------------------------------------------
# Вспомогательные функции
# ------------------------------------------------------------
def generate_hash(seed: str) -> str:
    return hashlib.md5(seed.encode()).hexdigest()

def normalize_filename(filename: str) -> str:
    name, ext = os.path.splitext(filename)
    # транслитерация
    name = translit(name, 'ru', reversed=True)
     # оставляем буквы, цифры, заменяем остальное на _
    name = re.sub(r'[^a-zA-Z0-9]', '_', name)
    # убираем множественные подчёркивания
    name = re.sub(r'_+', '_', name)
    name = name[:50]
    return f"{name}{ext}"

# ------------------------------------------------------------
# Модели
# ------------------------------------------------------------
class PhotoAlbum(BaseAlbum):
    allow_downloads = models.BooleanField('Разрешить скачивание', default=True)

    class Meta:
        verbose_name = 'Фотоальбом'
        verbose_name_plural = 'Фотоальбомы'

    def get_cover_url(self):
        """Возвращает URL миниатюры обложки альбома."""
        if self.cover:
            return self.cover.get_thumbnail_url()
        first_photo = self.photos.filter(is_deleted=False).first()
        if first_photo:
            return first_photo.get_thumbnail_url()
        return ''
    
    def hard_delete(self):
        """Полное удаление альбома: удалить все фото (с файлами), папку альбома и запись."""
        # Удаляем все фотографии альбома
        for photo in Photo.all_objects.filter(album=self):
            photo.hard_delete()
        # Удаляем папку альбома, если она существует и пуста
        album_dir = os.path.join(settings.MEDIA_ROOT, f'photos/album_{self.pk}')
        if os.path.exists(album_dir):
            try:
                os.rmdir(album_dir)  # удаляет только пустую папку
            except OSError:
                # Папка не пуста — возможно, остались файлы (хотя все фото удалены)
                pass
        # Удаляем запись альбома
        super().hard_delete()

    def soft_delete(self):
        """Мягкое удаление альбома: скрыть альбом и все его фото (даже уже скрытые)."""
        if not self.is_deleted:
            self.is_deleted = True
            self.deleted_at = timezone.now()
            self.save()
            # Мягко удаляем все фотографии альбома (включая уже удалённые, это безопасно)
            for photo in Photo.all_objects.filter(album=self):
                photo.soft_delete()

    def restore(self):
        """Восстановить альбом и все его фотографии, которые были скрыты."""
        if self.is_deleted:
            self.is_deleted = False
            self.deleted_at = None
            self.save()
            # Восстанавливаем только те фото, у которых is_deleted=True
            for photo in Photo.all_objects.filter(album=self, is_deleted=True):
                photo.restore()


class Photo(BaseMediaItem):
    album = models.ForeignKey(
        PhotoAlbum,
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name='Альбом'
    )
    alt_text = models.CharField('Альтернативный текст', max_length=200, blank=True)
    is_favorite = models.BooleanField('Избранное', default=False)

    class Meta:
        verbose_name = 'Фотография'
        verbose_name_plural = 'Фотографии'
        ordering = ['position', 'uploaded_at']

    # --------------------------------------------------------
    # Генерация версий
    # --------------------------------------------------------
    def _generate_optimized(self, original_path: str, hash_name: str, ext: str):
        max_width = getattr(settings, 'PHOTO_OPTIMIZED_MAX_WIDTH', 1200)
        quality = getattr(settings, 'PHOTO_OPTIMIZED_QUALITY', 85)

        img = Image.open(original_path)
        orig_width, orig_height = img.size

        if orig_width > max_width:
            ratio = max_width / orig_width
            new_height = int(orig_height * ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

        folder = os.path.dirname(original_path)
        opt_path = os.path.join(folder, f"{hash_name}_opt{ext}")
        img.save(opt_path, quality=quality, optimize=True)

        opt_size = os.path.getsize(opt_path)
        opt_width, opt_height = img.size
        return opt_path, opt_size, opt_width, opt_height

    def _generate_thumbnail(self, original_path: str, hash_name: str, ext: str):
        thumb_size = getattr(settings, 'PHOTO_THUMBNAIL_SIZE', (200, 200))

        img = Image.open(original_path)
        img.thumbnail(thumb_size, Image.Resampling.LANCZOS)
        if img.size != thumb_size:
            left = (img.width - thumb_size[0]) / 2
            top = (img.height - thumb_size[1]) / 2
            right = left + thumb_size[0]
            bottom = top + thumb_size[1]
            img = img.crop((left, top, right, bottom))

        folder = os.path.dirname(original_path)
        thumb_path = os.path.join(folder, f"{hash_name}_th{ext}")
        img.save(thumb_path, quality=85, optimize=True)

        thumb_size_bytes = os.path.getsize(thumb_path)
        thumb_width, thumb_height = img.size
        return thumb_path, thumb_size_bytes, thumb_width, thumb_height

    # --------------------------------------------------------
    # Сохранение
    # --------------------------------------------------------
    def save(self, *args, **kwargs):
        if not self.album_id:
            super().save(*args, **kwargs)
            return

        # Если явно не указан автор загрузки, пытаемся взять владельца альбома
        if not self.uploaded_by and self.album and self.album.owner:
            self.uploaded_by = self.album.owner

        if hasattr(self, '_file') and self._file:
        # Устанавливаем оригинальное имя из имени файла
            self.original_name = normalize_filename(self._file.name)            

        if hasattr(self, '_file') and self._file:
            # Удаление старых файлов
            if self.pk:
                try:
                    old = Photo.objects.get(pk=self.pk)
                    for field in ['file_original', 'file_optimized', 'file_thumbnail']:
                        f = getattr(old, field)
                        if f and default_storage.exists(f.name):
                            default_storage.delete(f.name)
                except Photo.DoesNotExist:
                    pass

            # Генерация путей
            hash_seed = f"{self.album_id}{time.time()}{uuid.uuid4().hex}{self._file.name}"
            hash_name = generate_hash(hash_seed)
            ext = os.path.splitext(self._file.name)[1].lower()
            folder = f"photos/album_{self.album_id}"
            full_folder = os.path.join(settings.MEDIA_ROOT, folder)
            os.makedirs(full_folder, exist_ok=True)

            # Оригинал
            original_filename = f"{hash_name}{ext}"
            original_path = os.path.join(full_folder, original_filename)
            with open(original_path, 'wb') as f:
                for chunk in self._file.chunks():
                    f.write(chunk)

            # Метаданные оригинала
            img = Image.open(original_path)
            orig_width, orig_height = img.size
            orig_size = os.path.getsize(original_path)

            # Оптимизация и превью
            opt_path, opt_size, opt_width, opt_height = self._generate_optimized(original_path, hash_name, ext)
            thumb_path, thumb_size, thumb_width, thumb_height = self._generate_thumbnail(original_path, hash_name, ext)

            # Сохраняем пути
            self.file_original = os.path.join(folder, original_filename)
            self.file_optimized = os.path.join(folder, f"{hash_name}_opt{ext}")
            self.file_thumbnail = os.path.join(folder, f"{hash_name}_th{ext}")

            # Метаданные
            self.metadata = {
                'original': {
                    'size': orig_size,
                    'width': orig_width,
                    'height': orig_height,
                    'filename': original_filename,
                },
                'optimized': {
                    'size': opt_size,
                    'width': opt_width,
                    'height': opt_height,
                    'filename': f"{hash_name}_opt{ext}",
                },
                'thumbnail': {
                    'size': thumb_size,
                    'width': thumb_width,
                    'height': thumb_height,
                    'filename': f"{hash_name}_th{ext}",
                }
            }
            delattr(self, '_file')

        super().save(*args, **kwargs)

    # --------------------------------------------------------
    # URL-методы
    # --------------------------------------------------------
    def get_original_url(self):
        return self.file_original.url if self.file_original else ''

    def get_optimized_url(self):
        return self.file_optimized.url if self.file_optimized else ''

    def get_thumbnail_url(self):
        return self.file_thumbnail.url if self.file_thumbnail else ''

    # --------------------------------------------------------
    # Полное удаление (файлы + запись)
    # --------------------------------------------------------
    def hard_delete(self):
        for field in ['file_original', 'file_optimized', 'file_thumbnail']:
            f = getattr(self, field)
            if f and default_storage.exists(f.name):
                default_storage.delete(f.name)
        self.delete()