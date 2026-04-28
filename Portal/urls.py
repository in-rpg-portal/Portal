from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from profiles.forms import CustomPasswordChangeForm

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('profiles/', include('profiles.urls')),
    path('directories/', include('directories.urls')),
    
    # Кастомная форма смены пароля
    path('accounts/password_change/', 
         auth_views.PasswordChangeView.as_view(
            form_class=CustomPasswordChangeForm,
            template_name='registration/password_change_form.html'
         ), 
         name='password_change'),
    
    path('accounts/password_change/done/', 
         auth_views.PasswordChangeDoneView.as_view(
            template_name='registration/password_change_done.html'
         ), 
         name='password_change_done'),
    
    # Остальные стандартные маршруты
    path('accounts/', include('django.contrib.auth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)