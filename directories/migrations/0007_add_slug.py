# directories/migrations/0007_add_slug.py
from django.db import migrations, models
from django.utils.text import slugify

def generate_slugs(apps, schema_editor):
    Record = apps.get_model('directories', 'Record')
    # Получаем все записи, у которых еще нет slug (те, что были добавлены до этой миграции)
    for record in Record.objects.filter(slug__isnull=True):
        # Попробуем получить текстовое значение для читаемого slug
        # Для этого нужно обратиться к RecordValue, но в миграции связь может быть не готова.
        # Поэтому генерируем на основе id: record-<id>
        base_slug = f"record-{record.id}"
        slug = base_slug
        counter = 1
        while Record.objects.filter(slug=slug).exclude(pk=record.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        record.slug = slug
        record.save(update_fields=['slug'])

class Migration(migrations.Migration):

    dependencies = [
        ('directories', '0006_add_position_to_record'),  # убедитесь, что номер правильный
    ]

    operations = [
        # 1. Добавляем поле slug как nullable, без уникальности
        migrations.AddField(
            model_name='record',
            name='slug',
            field=models.SlugField(max_length=100, blank=True, null=True, verbose_name='Slug'),
        ),
        # 2. Заполняем slug для существующих записей
        migrations.RunPython(generate_slugs, reverse_code=migrations.RunPython.noop),
        # 3. Изменяем поле: делаем уникальным и обязательным
        migrations.AlterField(
            model_name='record',
            name='slug',
            field=models.SlugField(max_length=100, unique=True, blank=False, null=False, verbose_name='Slug'),
        ),
    ]