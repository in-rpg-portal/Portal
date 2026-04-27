from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import os

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
    
    def save(self, *args, **kwargs):
        # Проверяем, есть ли уже сохранённый профиль
        if self.pk:
            try:
                old_avatar = Profile.objects.get(pk=self.pk).avatar
                # Если аватар изменился и старый существовал
                if old_avatar and old_avatar != self.avatar:
                    # Удаляем старый файл
                    if os.path.isfile(old_avatar.path):
                        os.remove(old_avatar.path)
                        print(f"Старый аватар удалён: {old_avatar.path}")
            except Profile.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)

# Сигналы для автоматического создания профиля
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()