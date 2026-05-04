import hashlib
import os
import time
import uuid
from django.conf import settings
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.timezone import now

@require_POST
@csrf_exempt  # CKEditor 5 отправляет запросы без CSRF токена; при необходимости можно настроить
def custom_ckeditor_upload(request):
    """
    Кастомная загрузка файлов для CKEditor 5.
    Ожидает поле 'upload' в request.FILES.
    Возвращает JSON с полем 'url' (абсолютный путь к загруженному файлу).
    """
    if 'upload' not in request.FILES:
        return JsonResponse({'error': 'No file provided'}, status=400)

    uploaded_file = request.FILES['upload']
    # Определяем приложение (из resolver_match)
    app_name = None
    if request.resolver_match:
        app_name = request.resolver_match.app_name
    if not app_name:
        # fallback: можно извлечь из referer, но лучше задать default
        app_name = 'default'

    # Валидация расширения
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    allowed_extensions = getattr(settings, 'CKEDITOR_5_ALLOWED_EXTENSIONS', ['.jpg', '.jpeg', '.png', '.gif'])
    if ext not in allowed_extensions:
        return JsonResponse({'error': f'Неподдерживаемый формат. Разрешены: {", ".join(allowed_extensions)}'}, status=400)

    # Валидация размера (максимум в МБ, по умолчанию 5 МБ)
    max_size_mb = getattr(settings, 'CKEDITOR_5_MAX_SIZE_MB', 5)
    if uploaded_file.size > max_size_mb * 1024 * 1024:
        return JsonResponse({'error': f'Файл слишком большой. Максимум {max_size_mb} МБ.'}, status=400)

    # Генерация хеша
    hash_input = f"{app_name}{time.time()}{uuid.uuid4().hex}{uploaded_file.name}"
    hash_name = hashlib.md5(hash_input.encode()).hexdigest()
    new_filename = f"{hash_name}{ext}"

    # Путь для сохранения: media/{app_name}/{hash}.ext
    relative_path = os.path.join(app_name, new_filename)
    full_path = default_storage.save(relative_path, uploaded_file)

    # Формируем URL для доступа
    file_url = default_storage.url(full_path)

    # Возвращаем JSON в формате, ожидаемом CKEditor 5
    return JsonResponse({'url': file_url})