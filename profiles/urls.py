from django.urls import path
from . import views

app_name = 'profiles'

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('<int:pk>/', views.profile_detail, name='profile_detail'),
    path('edit/', views.profile_edit, name='profile_edit'),
    path('about/', views.about, name='about'),
]