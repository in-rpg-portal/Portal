from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.task_list, name='task_list'),
    path('create/', views.task_create, name='task_create'),
    path('<slug:slug>/', views.task_detail, name='task_detail'),
    path('<slug:slug>/edit/', views.task_edit, name='task_edit'),
    path('<slug:slug>/delete/', views.task_delete, name='task_delete'),
    path('<slug:slug>/vote/', views.task_vote, name='task_vote'),
    path('<slug:slug>/history/', views.task_history, name='task_history'),
    path('<slug:slug>/comments/', views.task_comments, name='task_comments'),
]