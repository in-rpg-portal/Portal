from django.contrib import admin
from django.contrib.admin import action
from django.utils import timezone
from .models import Directory, Field, Record, RecordValue

# Базовый класс для отображения всех объектов (включая удалённые)
class AllObjectsModelAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        # Используем менеджер all_objects, который возвращает все записи (в т.ч. is_deleted=True)
        return self.model.all_objects.all()

@admin.register(Directory)
class DirectoryAdmin(AllObjectsModelAdmin):
    list_display = ('name', 'slug', 'is_deleted', 'created_at')
    list_filter = ('is_deleted',)
    search_fields = ('name', 'slug')
    actions = ['soft_delete_selected', 'restore_selected', 'hard_delete_selected']

    @action(description='Мягко удалить выбранные справочники')
    def soft_delete_selected(self, request, queryset):
        for obj in queryset:
            obj.soft_delete()
        self.message_user(request, f"{queryset.count()} справочников мягко удалено.")

    @action(description='Восстановить выбранные справочники')
    def restore_selected(self, request, queryset):
        for obj in queryset:
            obj.restore()
        self.message_user(request, f"{queryset.count()} справочников восстановлено.")

    @action(description='Полностью удалить выбранные справочники (необратимо)')
    def hard_delete_selected(self, request, queryset):
        for obj in queryset:
            obj.hard_delete()
        self.message_user(request, f"{queryset.count()} справочников удалено навсегда.")

@admin.register(Field)
class FieldAdmin(AllObjectsModelAdmin):
    list_display = ('name', 'directory', 'field_type', 'is_required', 'max_length', 'is_deleted')
    list_filter = ('directory', 'field_type', 'is_deleted')
    actions = ['soft_delete_selected', 'restore_selected', 'hard_delete_selected']

    def soft_delete_selected(self, request, queryset):
        for obj in queryset:
            obj.soft_delete()
        self.message_user(request, f"{queryset.count()} полей мягко удалено.")

    def restore_selected(self, request, queryset):
        for obj in queryset:
            obj.restore()
        self.message_user(request, f"{queryset.count()} полей восстановлено.")

    def hard_delete_selected(self, request, queryset):
        for obj in queryset:
            obj.hard_delete()
        self.message_user(request, f"{queryset.count()} полей удалено навсегда.")

@admin.register(Record)
class RecordAdmin(AllObjectsModelAdmin):
    list_display = ('id', 'directory', 'is_deleted', 'created_at')
    list_filter = ('directory', 'is_deleted')
    actions = ['soft_delete_selected', 'restore_selected', 'hard_delete_selected']

    def soft_delete_selected(self, request, queryset):
        for obj in queryset:
            obj.soft_delete()
        self.message_user(request, f"{queryset.count()} записей мягко удалено.")

    def restore_selected(self, request, queryset):
        for obj in queryset:
            obj.restore()
        self.message_user(request, f"{queryset.count()} записей восстановлено.")

    def hard_delete_selected(self, request, queryset):
        for obj in queryset:
            obj.hard_delete()
        self.message_user(request, f"{queryset.count()} записей удалено навсегда.")

@admin.register(RecordValue)
class RecordValueAdmin(AllObjectsModelAdmin):
    list_display = ('record', 'field', 'value_preview', 'is_deleted')
    list_filter = ('field__directory', 'field', 'is_deleted')
    search_fields = ('value',)
    actions = ['soft_delete_selected', 'restore_selected', 'hard_delete_selected']

    def value_preview(self, obj):
        return obj.value[:50]
    value_preview.short_description = 'Значение'

    def soft_delete_selected(self, request, queryset):
        for obj in queryset:
            obj.soft_delete()
        self.message_user(request, f"{queryset.count()} значений мягко удалено.")

    def restore_selected(self, request, queryset):
        for obj in queryset:
            obj.restore()
        self.message_user(request, f"{queryset.count()} значений восстановлено.")

    def hard_delete_selected(self, request, queryset):
        for obj in queryset:
            obj.hard_delete()
        self.message_user(request, f"{queryset.count()} значений удалено навсегда.")