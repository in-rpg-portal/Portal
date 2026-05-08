# Приложение «Справочники» (directories)

## Общее описание

`directories` — гибкая система для создания и управления динамическими справочниками.  
Позволяет определять произвольные поля (типы: короткая строка, текст с форматированием, число, дата, булево, ссылка на другой справочник, изображение), организовывать записи, применять мягкое и полное удаление, а также настраивать права доступа.

## Основные возможности

- **Динамические поля** – типы полей настраиваются через интерфейс (без программирования).
- **Поддержка изображений** – загрузка изображений, создание миниатюр с индивидуальными размерами, удаление старых файлов при замене.
- **WYSIWYG‑редактор** – для полей типа «Текст» используется CKEditor 5 с кастомной загрузкой изображений.
- **Короткие строки** – поле типа «Короткая строка» с настраиваемой максимальной длиной.
- **Сортировка записей** – числовое поле `position` (чем больше, тем выше) для ручного управления порядком.
- **Soft delete** – все объекты могут быть скрыты (не удаляются физически), каскадное скрытие записей при скрытии справочника.
- **Hard delete** – полное удаление с очисткой файлов (доступно только администраторам).
- **Права доступа** – стандартные (`view`, `add`, `change`, `delete`) и кастомные (`can_soft_delete_*`, `can_hard_delete_*`, `can_restore_*`) для справочников, полей и записей.

## Модели

### Directory (Справочник)
- `name`, `slug` – название и системное имя (уникально)
- `description` – описание
- `is_deleted`, `deleted_at` – флаги мягкого удаления
- `created_at`, `updated_at` – даты

### Field (Поле справочника)
- `directory` – внешний ключ на `Directory`
- `name`, `description`
- `field_type` – выбор типа: `string` (короткая строка), `text` (текст с CKEditor), `number`, `date`, `boolean`, `reference`, `image`
- `reference_directory` – для типа `reference` (на какой справочник ссылаться)
- `is_required` – обязательность поля
- `position` – порядок полей (0 = первый)
- **Для типа `image`:**  
  - `thumb_width`, `thumb_height` – размеры миниатюры в пикселях  
  - `max_size_mb` – максимальный размер загружаемого файла  
- **Для типа `string`:**  
  - `max_length` – максимальное количество символов
- `is_deleted`, `deleted_at` – мягкое удаление

### Record (Запись справочника)
- `directory` – внешний ключ на `Directory`
- `position` – число для сортировки записей (чем больше, тем выше)
- `is_default` – признак «запись по умолчанию» (уникален в пределах справочника)
- `is_deleted`, `deleted_at`
- `created_at`, `updated_at`
- `slug` – уникальный идентификатор для URL (генерируется автоматически)

### RecordValue (Значение поля для записи)
- `record` – внешний ключ на `Record`
- `field` – внешний ключ на `Field`
- `value` – строковое представление значения (для изображений – путь к файлу)
- `is_deleted`, `deleted_at`

## URL-маршруты

| URL | Назначение |
|-----|-------------|
| `/directories/` | Список справочников |
| `/directories/create/` | Создание справочника |
| `/directories/<slug>/edit/` | Редактирование справочника |
| `/directories/<slug>/delete/` | Мягкое удаление |
| `/directories/<slug>/restore/` | Восстановление (только админы) |
| `/directories/<slug>/hard_delete/` | Полное удаление (только админы) |
| `/directories/<slug>/fields/` | Список полей справочника |
| `/directories/<slug>/fields/create/` | Создание поля |
| `/directories/<slug>/fields/<pk>/edit/` | Редактирование поля |
| `/directories/<slug>/fields/<pk>/delete/` | Мягкое удаление поля |
| `/directories/<slug>/fields/<pk>/restore/` | Восстановление поля |
| `/directories/<slug>/fields/<pk>/hard_delete/` | Полное удаление поля |
| `/directories/<slug>/records/` | Список записей справочника (сортировка по `position` убывание) |
| `/directories/<slug>/records/create/` | Создание записи |
| `/directories/<slug>/records/<pk>/` | Детальный просмотр записи |
| `/directories/<slug>/records/<pk>/edit/` | Редактирование записи |
| `/directories/<slug>/records/<pk>/delete/` | Мягкое удаление записи |
| `/directories/<slug>/records/<pk>/restore/` | Восстановление записи |
| `/directories/<slug>/records/<pk>/hard_delete/` | Полное удаление записи |

## Представления

Все представления – function‑based, используют декораторы проверки прав (`@permission_required`, `@staff_member_required`).

- **directory_list** – список справочников
- **directory_create**, **directory_edit**, **directory_soft_delete**, **directory_restore**, **directory_hard_delete**
- **field_list**, **field_create**, **field_edit**, **field_soft_delete**, **field_restore**, **field_hard_delete**
- **record_list** – список записей справочника (передаются `records_data` с позициями и значениями текстовых/изображений)
- **record_create**, **record_edit**, **record_detail**, **record_soft_delete**, **record_restore**, **record_hard_delete**

## Формы

- **DirectoryForm** – создание/редактирование справочника
- **FieldForm** – динамическая форма с настройками в зависимости от типа поля (max_length для строки, размеры для изображения, выбор справочника для ссылки)
- **RecordForm** – форма, генерирующая поля на основе определённых в справочнике. Поддерживает все типы, включая CKEditor для текста, загрузку изображений с валидацией, выбор записей для ссылок. Также содержит поле `position` и `is_default` (доступно только администраторам).

## Утилиты (`utils.py`)

- `save_image_with_thumbnail` – сохраняет оригинал и создаёт миниатюру заданного размера, возвращает относительный путь.
- `delete_image_and_thumbnail` – удаляет оба файла.
- `generate_hash` – хеширование имён файлов.
- `pretty_html` – форматирует HTML‑код для читаемого хранения.

## Права доступа (permissions)

- **Для Directory:**  
  - `can_soft_delete_directory`, `can_hard_delete_directory`, `can_restore_directory`
- **Для Field:**  
  - `can_soft_delete_field`, `can_hard_delete_field`, `can_restore_field`
- **Для Record:**  
  - `can_soft_delete_record`, `can_hard_delete_record`, `can_restore_record`

Стандартные права (`view`, `add`, `change`, `delete`) также определены.  
В публичных формах поля `position`, `is_default`, `slug` редактируются только администраторами.

## Хранение изображений

- Путь: `media/directories/<directory_slug>/<hash>.<ext>`
- Миниатюра: `<hash>_th.<ext>`
- При обновлении изображения старые файлы удаляются.
- При `hard_delete` записи или поля файлы также удаляются.

