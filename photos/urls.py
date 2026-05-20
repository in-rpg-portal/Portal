from django.urls import path
from . import views

app_name = 'photos'

urlpatterns = [
    path('', views.album_list, name='album_list'),
    # Альбомы: создание, детали, редактирование, удаление
    path('album/create/', views.album_create, name='album_create'),
    path('album/<int:pk>/', views.album_detail, name='album_detail'),
    path('album/<int:pk>/edit/', views.album_edit, name='album_edit'),
    path('album/<int:pk>/delete/', views.album_delete, name='album_delete'),
    path('album/<int:pk>/add/', views.photo_add, name='photo_add'),
    # Фотографии
    path('photo/<int:pk>/', views.photo_detail, name='photo_detail'),
    path('photo/<int:pk>/edit/', views.photo_edit, name='photo_edit'),
    path('photo/<int:pk>/delete/', views.photo_delete, name='photo_delete'),
    path('photo/<int:pk>/like/', views.photo_like, name='photo_like'),
]