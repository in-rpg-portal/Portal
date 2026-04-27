from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import os
import hashlib
from django.utils import timezone

class Profile(models.Model):
    """Профиль пользователя, расширяющий стандартную модель User"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    bio = models.TextField('О себе', max_length=500, blank=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    avatar = models.ImageField(
        'Аватар', 
        upload_to='avatars/', 
        blank=True, 
        null=True,
        help_text='Загрузите изображение (jpg, png, gif) до 1MB'
    )
    
    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'
    
    def __str__(self):
        return f'Профиль пользователя {self.user.username}'
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('profiles:profile_detail', args=[self.pk])
    
    def delete_old_avatar(self):
        """Удаляет старый файл аватара, если он существует"""
        if self.avatar and os.path.isfile(self.avatar.path):
            try:
                os.remove(self.avatar.path)
                print(f"Старый аватар удалён: {self.avatar.path}")
            except Exception as e:
                print(f"Ошибка удаления аватара: {e}")
    
    def save(self, *args, **kwargs):
        # Если профиль уже существует (есть pk), проверяем аватар
        if self.pk:
            try:
                old_avatar = Profile.objects.get(pk=self.pk).avatar
                # Если аватар изменился и старый существовал
                if old_avatar and old_avatar != self.avatar:
                    if os.path.isfile(old_avatar.path):
                        os.remove(old_avatar.path)
                        print(f"Старый аватар удалён при сохранении: {old_avatar.path}")
            except Profile.DoesNotExist:
                pass
        super().save(*args, **kwargs)

# Сигналы
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()