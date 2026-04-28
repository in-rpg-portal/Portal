from django.urls import path
from . import views

app_name = 'directories'

urlpatterns = [
    # Справочники
    path('', views.directory_list, name='directory_list'),
    path('create/', views.directory_create, name='directory_create'),
    path('<slug:slug>/edit/', views.directory_edit, name='directory_edit'),
    path('<slug:slug>/delete/', views.directory_soft_delete, name='directory_soft_delete'),
    path('<slug:slug>/restore/', views.directory_restore, name='directory_restore'),
    path('<slug:slug>/hard_delete/', views.directory_hard_delete, name='directory_hard_delete'),

    # Поля
    path('<slug:slug>/fields/', views.field_list, name='field_list'),
    path('<slug:slug>/fields/create/', views.field_create, name='field_create'),
    path('<slug:slug>/fields/<int:pk>/edit/', views.field_edit, name='field_edit'),
    path('<slug:slug>/fields/<int:pk>/delete/', views.field_soft_delete, name='field_soft_delete'),
    path('<slug:slug>/fields/<int:pk>/restore/', views.field_restore, name='field_restore'),
    # Для hard delete полей можно добавить отдельный путь, но используем delete? По аналогии со справочниками добавим:
    path('<slug:slug>/fields/<int:pk>/hard_delete/', views.field_hard_delete, name='field_hard_delete'),

    # Записи
    path('<slug:slug>/records/', views.record_list, name='record_list'),
    path('<slug:slug>/records/create/', views.record_create, name='record_create'),
    path('<slug:slug>/records/<int:pk>/', views.record_detail, name='record_detail'),
    path('<slug:slug>/records/<int:pk>/edit/', views.record_edit, name='record_edit'),
    path('<slug:slug>/records/<int:pk>/delete/', views.record_soft_delete, name='record_soft_delete'),
    path('<slug:slug>/records/<int:pk>/restore/', views.record_restore, name='record_restore'),
    path('<slug:slug>/records/<int:pk>/hard_delete/', views.record_hard_delete, name='record_hard_delete'),
]