from django.db import migrations, models

def set_position_from_id(apps, schema_editor):
    Record = apps.get_model('directories', 'Record')
    for record in Record.objects.all():
        record.position = record.id
        record.save(update_fields=['position'])

class Migration(migrations.Migration):

    dependencies = [
        ('directories', '0005_record_is_default'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='record',
            options={'ordering': ['-position', 'id'], 'permissions': [('can_soft_delete_record', 'Может мягко удалять запись'), ('can_hard_delete_record', 'Может полностью удалять запись'), ('can_restore_record', 'Может восстанавливать запись')], 'verbose_name': 'Запись справочника', 'verbose_name_plural': 'Записи справочников'},
        ),
        migrations.AddField(
            model_name='record',
            name='position',
            field=models.PositiveIntegerField(db_index=True, default=0, help_text='Чем больше число, тем выше запись в списке.', verbose_name='Позиция'),
        ),
        migrations.RunPython(set_position_from_id, migrations.RunPython.noop),
    ]