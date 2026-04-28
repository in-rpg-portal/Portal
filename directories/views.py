from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required, permission_required
from django.urls import reverse
from .models import Directory, Field, Record
from .forms import DirectoryForm, FieldForm, RecordForm

# ----- Справочники -----
def directory_list(request):
    """Список справочников (только активные)"""
    directories = Directory.objects.all()
    return render(request, 'directories/directory_list.html', {'directories': directories})

@permission_required('directories.can_add_directory', raise_exception=True)
def directory_create(request):
    if request.method == 'POST':
        form = DirectoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Справочник успешно создан.')
            return redirect('directories:directory_list')
    else:
        form = DirectoryForm()
    return render(request, 'directories/directory_form.html', {'form': form, 'title': 'Создать справочник'})

@permission_required('directories.can_change_directory', raise_exception=True)
def directory_edit(request, slug):
    directory = get_object_or_404(Directory, slug=slug)
    if request.method == 'POST':
        form = DirectoryForm(request.POST, instance=directory)
        if form.is_valid():
            form.save()
            messages.success(request, 'Справочник обновлён.')
            return redirect('directories:directory_list')
    else:
        form = DirectoryForm(instance=directory)
    return render(request, 'directories/directory_form.html', {'form': form, 'title': 'Редактировать справочник'})

@staff_member_required
def directory_soft_delete(request, slug):
    directory = get_object_or_404(Directory, slug=slug)
    if request.method == 'POST':
        delete_type = request.POST.get('delete_type')
        if delete_type == 'hard' and request.user.has_perm('directories.can_hard_delete_directory'):
            directory.hard_delete()
            messages.success(request, f'Справочник "{directory.name}" полностью удалён.')
        else:
            directory.soft_delete()
            messages.success(request, f'Справочник "{directory.name}" мягко удалён (скрыт).')
        return redirect('directories:directory_list')
    return render(request, 'directories/directory_confirm_delete.html', {'object': directory})

@staff_member_required
def directory_restore(request, slug):
    directory = get_object_or_404(Directory.all_objects, slug=slug, is_deleted=True)
    if request.user.has_perm('directories.can_restore_directory'):
        directory.restore()
        messages.success(request, f'Справочник "{directory.name}" восстановлен.')
    else:
        messages.error(request, 'Недостаточно прав для восстановления.')
    return redirect('directories:directory_list')

@staff_member_required
def directory_hard_delete(request, slug):
    directory = get_object_or_404(Directory.all_objects, slug=slug, is_deleted=True)
    if request.user.has_perm('directories.can_hard_delete_directory'):
        directory.hard_delete()
        messages.success(request, f'Справочник "{directory.name}" полностью удалён.')
    else:
        messages.error(request, 'Недостаточно прав для полного удаления.')
    return redirect('directories:directory_list')

# ----- Поля -----
def field_list(request, slug):
    directory = get_object_or_404(Directory, slug=slug)
    fields = directory.fields.all()
    return render(request, 'directories/field_list.html', {'directory': directory, 'fields': fields})

@permission_required('directories.can_add_field', raise_exception=True)
def field_create(request, slug):
    directory = get_object_or_404(Directory, slug=slug)
    if request.method == 'POST':
        form = FieldForm(request.POST)
        form.instance.directory = directory   # <-- Устанавливаем директорию ДО валидации
        if form.is_valid():
            field = form.save()
            messages.success(request, f'Поле "{field.name}" создано.')
            return redirect('directories:field_list', slug=directory.slug)
    else:
        form = FieldForm()
    return render(request, 'directories/field_form.html', {'form': form, 'directory': directory, 'title': 'Создать поле'})

@permission_required('directories.can_change_field', raise_exception=True)
def field_edit(request, slug, pk):
    directory = get_object_or_404(Directory, slug=slug)
    field = get_object_or_404(Field, pk=pk, directory=directory)
    if request.method == 'POST':
        form = FieldForm(request.POST, instance=field)
        if form.is_valid():
            form.save()
            messages.success(request, 'Поле обновлено.')
            return redirect('directories:field_list', slug=directory.slug)
    else:
        form = FieldForm(instance=field)
    return render(request, 'directories/field_form.html', {'form': form, 'directory': directory, 'title': 'Редактировать поле'})

@staff_member_required
def field_soft_delete(request, slug, pk):
    field = get_object_or_404(Field, pk=pk, directory__slug=slug)
    if request.method == 'POST':
        delete_type = request.POST.get('delete_type')
        if delete_type == 'hard' and request.user.has_perm('directories.can_hard_delete_field'):
            field.hard_delete()
            messages.success(request, f'Поле "{field.name}" полностью удалено.')
        else:
            field.soft_delete()
            messages.success(request, f'Поле "{field.name}" мягко удалено.')
        return redirect('directories:field_list', slug=slug)
    return render(request, 'directories/field_confirm_delete.html', {'field': field, 'directory': field.directory})

@staff_member_required
def field_restore(request, slug, pk):
    field = get_object_or_404(Field.all_objects, pk=pk, directory__slug=slug, is_deleted=True)
    if request.user.has_perm('directories.can_restore_field'):
        field.restore()
        messages.success(request, f'Поле "{field.name}" восстановлено.')
    else:
        messages.error(request, 'Недостаточно прав для восстановления.')
    return redirect('directories:field_list', slug=slug)

@staff_member_required
def field_hard_delete(request, slug, pk):
    field = get_object_or_404(Field.all_objects, pk=pk, directory__slug=slug, is_deleted=True)
    if request.user.has_perm('directories.can_hard_delete_field'):
        field.hard_delete()
        messages.success(request, f'Поле "{field.name}" полностью удалено.')
    else:
        messages.error(request, 'Недостаточно прав для полного удаления.')
    return redirect('directories:field_list', slug=slug)

# ----- Записи -----
def record_list(request, slug):
    directory = get_object_or_404(Directory, slug=slug)
    records = directory.records.all()
    text_field = directory.fields.filter(field_type='text').first()
    image_field = directory.fields.filter(field_type='image').first()
    
    records_data = []
    for record in records:
        data = {'record': record}
        if text_field:
            text_value = record.values.filter(field=text_field, is_deleted=False).first()
            data['text_value'] = text_value.value if text_value else ''
        if image_field:
            image_value = record.values.filter(field=image_field, is_deleted=False).first()
            data['image_path'] = image_value.value if image_value else ''
        records_data.append(data)
    
    return render(request, 'directories/record_list.html', {
        'directory': directory,
        'records_data': records_data,
        'text_field': text_field,
        'image_field': image_field,
    })

@permission_required('directories.can_add_record', raise_exception=True)
def record_create(request, slug):
    directory = get_object_or_404(Directory, slug=slug)
    if request.method == 'POST':
        form = RecordForm(directory, request.POST, request.FILES)
        if form.is_valid():
            record = form.save(commit=False)
            record.directory = directory
            record.save()
            form.save()  # сохраняет значения полей
            messages.success(request, 'Запись создана.')
            return redirect('directories:record_list', slug=directory.slug)
    else:
        form = RecordForm(directory)
    return render(request, 'directories/record_form.html', {'form': form, 'directory': directory, 'title': 'Создать запись'})

@permission_required('directories.can_change_record', raise_exception=True)
def record_edit(request, slug, pk):
    directory = get_object_or_404(Directory, slug=slug)
    record = get_object_or_404(Record, pk=pk, directory=directory)
    if request.method == 'POST':
        form = RecordForm(directory, request.POST, request.FILES, instance=record)
        if form.is_valid():
            form.save()
            messages.success(request, 'Запись обновлена.')
            return redirect('directories:record_list', slug=directory.slug)
    else:
        form = RecordForm(directory, instance=record)
    return render(request, 'directories/record_form.html', {'form': form, 'directory': directory, 'title': 'Редактировать запись'})

def record_detail(request, slug, pk):
    directory = get_object_or_404(Directory, slug=slug)
    record = get_object_or_404(Record, pk=pk, directory=directory)
    values = record.values.select_related('field').filter(is_deleted=False)
    # Преобразуем значения для шаблона
    values_data = []
    for v in values:
        display = v.value
        if v.field.field_type == 'boolean':
            display = 'Да' if v.value == 'True' else 'Нет'
        elif v.field.field_type == 'reference' and v.value:
            try:
                ref_record = Record.objects.get(pk=int(v.value))
                display = str(ref_record)
            except:
                display = f'[Удалено] #{v.value}'
        elif v.field.field_type == 'image' and v.value:
            display = v.value  # путь к оригиналу
        values_data.append({'field': v.field, 'value': v.value, 'display': display})
    return render(request, 'directories/record_detail.html', {
        'directory': directory,
        'record': record,
        'values': values_data,
    })

@staff_member_required
def record_soft_delete(request, slug, pk):
    record = get_object_or_404(Record, pk=pk, directory__slug=slug)
    if request.method == 'POST':
        delete_type = request.POST.get('delete_type')
        if delete_type == 'hard' and request.user.has_perm('directories.can_hard_delete_record'):
            record.hard_delete()
            messages.success(request, f'Запись #{record.id} полностью удалена.')
        else:
            record.soft_delete()
            messages.success(request, f'Запись #{record.id} мягко удалена.')
        return redirect('directories:record_list', slug=slug)
    return render(request, 'directories/record_confirm_delete.html', {'record': record, 'directory': record.directory})

@staff_member_required
def record_restore(request, slug, pk):
    record = get_object_or_404(Record.all_objects, pk=pk, directory__slug=slug, is_deleted=True)
    if request.user.has_perm('directories.can_restore_record'):
        record.restore()
        messages.success(request, f'Запись #{record.id} восстановлена.')
    else:
        messages.error(request, 'Недостаточно прав для восстановления.')
    return redirect('directories:record_list', slug=slug)

@staff_member_required
def record_hard_delete(request, slug, pk):
    record = get_object_or_404(Record.all_objects, pk=pk, directory__slug=slug, is_deleted=True)
    if request.user.has_perm('directories.can_hard_delete_record'):
        record.hard_delete()
        messages.success(request, f'Запись #{record.id} полностью удалена.')
    else:
        messages.error(request, 'Недостаточно прав для полного удаления.')
    return redirect('directories:record_list', slug=slug)