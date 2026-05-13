from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseNotAllowed
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
            album.save()
            messages.success(request, f'Альбом "{album.title}" успешно создан.')
            return redirect('photos:album_detail', pk=album.pk)
    else:
        form = PhotoAlbumForm()
    return render(request, 'photos/album_form.html', {'form': form, 'title': 'Создать альбом'})

def album_detail(request, pk):
    # Временная заглушка
    album = get_object_or_404(PhotoAlbum, pk=pk, is_deleted=False)
    return render(request, 'photos/temp_message.html', {'message': f'Детали альбома "{album.title}" — в разработке'})

@login_required
def album_edit(request, pk):
    # Временная заглушка
    return render(request, 'photos/temp_message.html', {'message': 'Редактирование альбома — в разработке'})

@login_required
def album_delete(request, pk):
    # Временная заглушка
    return render(request, 'photos/temp_message.html', {'message': 'Удаление альбома — в разработке'})

@login_required
def photo_add(request, pk):
    # Временная заглушка
    return render(request, 'photos/temp_message.html', {'message': 'Добавление фото — в разработке'})

def photo_detail(request, pk):
    # Временная заглушка
    photo = get_object_or_404(Photo, pk=pk, is_deleted=False)
    return render(request, 'photos/temp_message.html', {'message': f'Детали фото "{photo.original_name}" — в разработке'})

@login_required
def photo_edit(request, pk):
    # Временная заглушка
    return render(request, 'photos/temp_message.html', {'message': 'Редактирование фото — в разработке'})

@login_required
def photo_delete(request, pk):
    # Временная заглушка
    return render(request, 'photos/temp_message.html', {'message': 'Удаление фото — в разработке'})