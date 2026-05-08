from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    # Основные списки
    path('', views.task_list, name='task_list'),                     # активные
    path('all/', views.task_list_all, name='task_list_all'),         # все

    # Создание
    path('create/', views.task_create, name='task_create'),

    # Детальные страницы по числовому ID (должны быть первыми, чтобы не перехватывались slug)
    path('<int:pk>/', views.task_detail, name='task_detail'),
    path('<int:pk>/edit/', views.task_edit, name='task_edit'),
    path('<int:pk>/resolve/', views.task_resolve, name='task_resolve'),
    path('<int:pk>/delete/', views.task_delete, name='task_delete'),
    path('<int:pk>/vote/', views.task_vote, name='task_vote'),
    path('<int:pk>/history/', views.task_history, name='task_history'),
    path('<int:pk>/comments/', views.task_comments, name='task_comments'),


    # Фильтр по slug (тип/приоритет/статус) – в конце
    path('<slug:slug>/', views.task_list_filtered, name='task_list_filtered'),
]