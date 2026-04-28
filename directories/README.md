## Проект: приложение directories для Django

- **Цель:** создать справочники с динамическими полями (текст, число, дата, булево, ссылка, изображение), мягким/полным удалением, кастомными правами.
- **Технологии:** Django 6.0, MySQL, Pillow.
- **Модели:** Directory (name, slug, description, is_deleted, deleted_at), Field (типы, reference, thumb_width/height, max_size_mb и т.д.), Record, RecordValue (value хранит строку, для изображений – путь).
- **Soft delete:** все модели имеют is_deleted, deleted_at; менеджеры: objects (только активные), all_objects (все).
- **Права:** стандартные + кастомные can_soft_delete_*, can_hard_delete_*, can_restore_* для каждой модели.
- **Изображения:** сохранение в media/directories/<slug>/<hash>.ext, миниатюра <hash>_th.ext, настройка размеров и max_size_mb для каждого поля. При замене старые файлы удаляются. Валидация форматов (jpg, png, gif).
- **Views:** function-based, полный CRUD, restore, hard_delete, проверка прав через @permission_required, декоратор @staff_member_required для административных действий.
- **URL:** используют slug справочника, например /directories/<slug>/records/<pk>/edit/.
- **Формы:** DirectoryForm, FieldForm, динамическая RecordForm (генерирует поля на основе Field). Исправлена ошибка field_create – добавлено `form.instance.directory = directory` до вызова `is_valid()`.
- **Шаблоны:** в `templates/directories/`, наследуют `base.html`, используют классы `form-input`, `btn-primary`, `content-card`.
- **Миграции:** была ошибка из-за рассинхрона между моделями и БД. Решено: удаление записей из `django_migrations` для `directories`, удаление таблиц, удаление старых миграций, пересоздание миграции и применение.
- **Админка:** переопределён `get_queryset` через `AllObjectsModelAdmin` с использованием `all_objects`, чтобы видеть мягко удалённые записи. Добавлены actions для soft/hard delete и restore.
- **Дополнительно:** подготовлен README.md по частям. Приложение интегрировано в проект (добавлено в INSTALLED_APPS, urlpatterns, левое меню).
- **Итог:** всё работает, справочники, поля, записи, включая изображения, soft/hard delete, права.

## Бриф проекта: приложение `directories`

**Сделано:**
- Модели `Directory`, `Field`, `Record`, `RecordValue` с soft delete, кастомными permissions, поддержкой полей тип `image` (с миниатюрами, настройками размеров и max_size).
- CRUD для справочников, полей, записей; динамическая генерация форм; полное и мягкое удаление; восстановление.
- URL на основе slug, views с проверкой прав, шаблоны в `templates/directories/`, статика (опционально).
- Утилиты для хеширования имён, обработки и удаления изображений.
- Админка с `all_objects` (видимость удалённых записей) и actions.

**Основные файлы:**
- `models.py`, `admin.py`, `forms.py`, `views.py`, `urls.py`, `utils.py`.
- Шаблоны: `*_list.html`, `*_form.html`, `*_confirm_delete.html`, `record_detail.html`.


