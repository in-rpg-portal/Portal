import hashlib
import os
import uuid
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.conf import settings
from PIL import Image
from io import BytesIO

def generate_hash(value: str) -> str:
    """Генерирует хеш из строки (slug + field_name + время + случайное)"""
    salt = uuid.uuid4().hex
    return hashlib.md5(f"{value}{salt}".encode()).hexdigest()

def save_image_with_thumbnail(uploaded_file: InMemoryUploadedFile,
                              directory_slug: str,
                              field_name: str,
                              thumb_width: int,
                              thumb_height: int,
                              max_size_mb: int):
    """
    Сохраняет оригинал изображения и миниатюру.
    Возвращает относительный путь к оригиналу (для хранения в RecordValue.value).
    """
    # Валидация расширения
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.gif']:
        raise ValueError("Неподдерживаемый формат изображения")

    # Валидация размера
    if uploaded_file.size > max_size_mb * 1024 * 1024:
        raise ValueError(f"Размер файла превышает {max_size_mb} Мб")

    # Генерация хеша для имени файла
    hash_name = generate_hash(f"{directory_slug}_{field_name}_{uploaded_file.name}")
    original_filename = f"{hash_name}{ext}"
    thumb_filename = f"{hash_name}_th{ext}"

    # Пути для сохранения
    media_root = settings.MEDIA_ROOT
    dir_path = os.path.join('directories', directory_slug)
    full_dir_path = os.path.join(media_root, dir_path)
    os.makedirs(full_dir_path, exist_ok=True)

    original_full_path = os.path.join(full_dir_path, original_filename)
    thumb_full_path = os.path.join(full_dir_path, thumb_filename)

    # Сохраняем оригинал
    with open(original_full_path, 'wb') as f:
        for chunk in uploaded_file.chunks():
            f.write(chunk)

    # Создаём миниатюру
    img = Image.open(original_full_path)
    img.thumbnail((thumb_width, thumb_height), Image.Resampling.LANCZOS)
    # Обрезка до точных размеров (центрированная)
    if img.width != thumb_width or img.height != thumb_height:
        left = (img.width - thumb_width) / 2
        top = (img.height - thumb_height) / 2
        right = left + thumb_width
        bottom = top + thumb_height
        img = img.crop((left, top, right, bottom))
    img.save(thumb_full_path, quality=90)

    # Возвращаем относительный путь к оригиналу для БД
    return os.path.join(dir_path, original_filename)

def delete_image_and_thumbnail(relative_path: str):
    """Удаляет оригинал и миниатюру по относительному пути оригинала"""
    if not relative_path:
        return
    media_root = settings.MEDIA_ROOT
    original_full = os.path.join(media_root, relative_path)
    dir_name = os.path.dirname(original_full)
    base, ext = os.path.splitext(os.path.basename(original_full))
    thumb_full = os.path.join(dir_name, f"{base}_th{ext}")
    for f in [original_full, thumb_full]:
        if os.path.exists(f):
            os.remove(f)