from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseNotAllowed
from django.db import models
from .models import PhotoAlbum, Photo
from .forms import PhotoAlbumForm, PhotoForm


def album_list(request):
    """Список публичных альбомов (сортировка по order, затем по created_at)"""
    albums = PhotoAlbum.objects.filter(privacy='public', is_deleted=False).order_by('-order', '-created_at')
    paginator = Paginator(albums, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'photos/album_list.html', {'page_obj': page_obj})

@login_required
def album_create(request):
    if request.method == 'POST':
        form = PhotoAlbumForm(request.POST)
        if form.is_valid():
            album = form.save(commit=False)
            album.owner = request.user
            if not album.slug:
                import uuid
                album.slug = uuid.uuid4().hex[:12]
            album.save()
            messages.success(request, f'Альбом "{album.title}" успешно создан.')
            return redirect('photos:album_detail', pk=album.pk)
    else:
        form = PhotoAlbumForm()
    return render(request, 'photos/album_form.html', {'form': form, 'title': 'Создать альбом'})

def album_detail(request, pk):
    album = get_object_or_404(PhotoAlbum, pk=pk, is_deleted=False)
    # Проверка доступа (метод has_access определен в BaseAlbum)
    if not album.has_access(request.user):
        raise PermissionDenied("У вас нет доступа к этому альбому.")

    # Получаем фотографии альбома, сортировка по position, uploaded_at
    photos = album.photos.filter(is_deleted=False).order_by('position', 'uploaded_at')
    paginator = Paginator(photos, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'photos/album_detail.html', {
        'album': album,
        'page_obj': page_obj,
    })

@login_required
def album_edit(request, pk):
    album = get_object_or_404(PhotoAlbum, pk=pk, is_deleted=False)
    # Проверка прав: владелец или админ
    if album.owner != request.user and not request.user.is_staff:
        raise PermissionDenied("Вы не можете редактировать этот альбом.")
    if request.method == 'POST':
        form = PhotoAlbumForm(request.POST, instance=album)
        if form.is_valid():
            form.save()
            messages.success(request, f'Альбом "{album.title}" обновлён.')
            return redirect('photos:album_detail', pk=album.pk)
    else:
        form = PhotoAlbumForm(instance=album)
    return render(request, 'photos/album_form.html', {'form': form, 'title': 'Редактировать альбом'})

@login_required
def album_delete(request, pk):
    album = get_object_or_404(PhotoAlbum, pk=pk)
    # Только администраторы могут удалять альбомы
    if not request.user.is_staff:
        raise PermissionDenied("У вас недостаточно прав для удаления альбома.")
    
    if request.method == 'POST':
        delete_type = request.POST.get('delete_type')
        if delete_type == 'hard':
            album.hard_delete()
            messages.success(request, f'Альбом "{album.title}" полностью удалён (безвозвратно).')
        else:
            album.soft_delete()
            messages.success(request, f'Альбом "{album.title}" мягко удалён (скрыт).')
        return redirect('photos:album_list')
    
    return render(request, 'photos/album_confirm_delete.html', {'album': album})

@login_required
def photo_add(request, pk):
    album = get_object_or_404(PhotoAlbum, pk=pk, is_deleted=False)
    if album.owner != request.user and not request.user.is_staff:
        raise PermissionDenied("Вы не можете добавлять фото в этот альбом.")
    
    if request.method == 'POST':
        files = request.FILES.getlist('images')
        if not files:
            messages.error(request, 'Выберите хотя бы одно изображение.')
            return redirect('photos:photo_add', pk=album.pk)
        
        success_count = 0
        for file in files:
            photo = Photo(album=album, uploaded_by=request.user)
            photo._file = file
            # Определяем позицию: следующий номер после существующих
            last_position = album.photos.filter(is_deleted=False).aggregate(models.Max('position'))['position__max'] or 0
            photo.position = last_position + 1
            photo.save()  # внутри save() обработает _file и создаст файлы
            success_count += 1
        
        messages.success(request, f'Успешно загружено {success_count} фотографий.')
        return redirect('photos:album_detail', pk=album.pk)
    
    return render(request, 'photos/photo_add.html', {'album': album})

def photo_detail(request, pk):
    photo = get_object_or_404(Photo, pk=pk, is_deleted=False)
    # Проверка доступа к альбому
    if not photo.album.has_access(request.user):
        raise PermissionDenied("У вас нет доступа к этому фото.")
    
    # Увеличиваем счётчик просмотров
    photo.view_count += 1
    photo.save(update_fields=['view_count'])
    
    # Навигация: предыдущее и следующее фото в альбоме
    photos_in_album = photo.album.photos.filter(is_deleted=False).order_by('position', 'uploaded_at')
    photo_list = list(photos_in_album)
    current_index = None
    for i, p in enumerate(photo_list):
        if p.pk == photo.pk:
            current_index = i
            break
    prev_photo = photo_list[current_index - 1] if current_index > 0 else None
    next_photo = photo_list[current_index + 1] if current_index < len(photo_list) - 1 else None
    
    # Комментарии (пока без формы, только отображение)
    #comments = photo.comments.filter(is_deleted=False)  # если модель PhotoComment ещё не создана, закомментировать
    
    return render(request, 'photos/photo_detail.html', {
        'photo': photo,
        'prev_photo': prev_photo,
        'next_photo': next_photo,
        #'comments': comments,
    })

@login_required
def photo_edit(request, pk):
    # Временная заглушка
    return render(request, 'photos/temp_message.html', {'message': 'Редактирование фото — в разработке'})

@login_required
def photo_delete(request, pk):
    # Временная заглушка
    return render(request, 'photos/temp_message.html', {'message': 'Удаление фото — в разработке'})