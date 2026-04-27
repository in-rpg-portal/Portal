from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User
from .models import Profile
import re
import hashlib
import os
from django.utils import timezone

class SignUpForm(UserCreationForm):
    """Улучшенная форма регистрации нового пользователя с аватаром"""
    
    username = forms.CharField(
        label='Имя пользователя',
        max_length=150,
        min_length=3,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Введите имя пользователя',
            'autocomplete': 'off'
        }),
        help_text='Только буквы, цифры и символы @/./+/-/_. От 3 до 150 символов.'
    )
    
    email = forms.EmailField(
        label='Электронная почта',
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'user@example.com',
            'autocomplete': 'off'
        }),
        help_text='Введите действующий email. Потребуется для восстановления пароля.'
    )
    
    password1 = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Введите пароль',
            'autocomplete': 'new-password'
        }),
        help_text='Минимум 8 символов. Пароль не должен быть слишком простым.'
    )
    
    password2 = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Повторите пароль',
            'autocomplete': 'new-password'
        }),
        help_text='Введите тот же пароль, что и выше.'
    )
    
    bio = forms.CharField(
        label='О себе',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'rows': 4,
            'placeholder': 'Расскажите немного о себе, своих игровых предпочтениях...'
        }),
        help_text='Необязательное поле. Максимум 500 символов.'
    )
    
    avatar = forms.ImageField(
        label='Аватар',
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-input',
            'accept': 'image/jpeg,image/png,image/gif'
        }),
        help_text='Необязательно. Поддерживаются JPEG, PNG, GIF до 1MB.'
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'bio', 'avatar')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = 'Только буквы, цифры и символы @/./+/-/_. От 3 до 150 символов.'
        self.fields['password1'].help_text = 'Минимум 8 символов. Пароль не должен быть слишком простым.'
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not re.match(r'^[\w.@+-]+$', username):
            raise forms.ValidationError('Имя пользователя может содержать только буквы, цифры и символы @/./+/-/_.')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('Пользователь с таким именем уже существует.')
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            if User.objects.filter(email__iexact=email).exists():
                raise forms.ValidationError('Пользователь с таким email уже зарегистрирован.')
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                raise forms.ValidationError('Введите корректный email адрес.')
        return email
    
    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if password:
            if len(password) < 8:
                raise forms.ValidationError('Пароль должен содержать минимум 8 символов.')
            common_passwords = ['password', '12345678', 'qwerty123', 'admin123']
            if password.lower() in common_passwords:
                raise forms.ValidationError('Пароль слишком простой. Придумайте более сложный пароль.')
            if not any(char.isdigit() for char in password):
                raise forms.ValidationError('Пароль должен содержать хотя бы одну цифру.')
            if not any(char.isalpha() for char in password):
                raise forms.ValidationError('Пароль должен содержать хотя бы одну букву.')
        return password
    
    def clean_bio(self):
        bio = self.cleaned_data.get('bio')
        if bio and len(bio) > 500:
            raise forms.ValidationError('Описание не может превышать 500 символов.')
        return bio
    
    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            if avatar.size > 1 * 1024 * 1024:
                raise forms.ValidationError('Размер файла не должен превышать 1MB.')
            valid_types = ['image/jpeg', 'image/png', 'image/gif']
            if avatar.content_type not in valid_types:
                raise forms.ValidationError('Поддерживаются только JPEG, PNG и GIF изображения.')
            
            # Генерируем хеш для имени файла (НО НЕ СОХРАНЯЕМ ЗДЕСЬ)
            ext = os.path.splitext(avatar.name)[1].lower()
            unique_string = f"temp_{timezone.now().timestamp()}"
            hash_name = hashlib.md5(unique_string.encode()).hexdigest() + ext
            avatar.name = hash_name
        
        return avatar
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            profile = user.profile
            profile.bio = self.cleaned_data.get('bio', '')
            avatar = self.cleaned_data.get('avatar')
            if avatar:
                # Генерируем финальное имя с username пользователя
                ext = os.path.splitext(avatar.name)[1].lower()
                unique_string = f"{user.username}_{timezone.now().timestamp()}"
                hash_name = hashlib.md5(unique_string.encode()).hexdigest() + ext
                avatar.name = hash_name
                profile.avatar = avatar
            profile.save()
        return user


class ProfileEditForm(forms.ModelForm):
    """Форма редактирования профиля с переименованием аватара в хеш"""
    
    class Meta:
        model = Profile
        fields = ('bio', 'avatar')
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-input', 'rows': 6, 'placeholder': 'Расскажите о себе...'}),
            'avatar': forms.FileInput(attrs={'class': 'form-input', 'accept': 'image/*'}),
        }
        labels = {
            'bio': 'О себе',
            'avatar': 'Аватар',
        }
    
    def clean_avatar(self):
        """Валидация и переименование аватара при загрузке"""
        avatar = self.cleaned_data.get('avatar')
        
        if avatar:
            # Проверка размера файла (не более 1MB)
            if avatar.size > 1 * 1024 * 1024:
                raise forms.ValidationError('Размер файла не должен превышать 1MB')
            
            # Проверка типа файла
            valid_types = ['image/jpeg', 'image/png', 'image/gif']
            if avatar.content_type not in valid_types:
                raise forms.ValidationError('Поддерживаются только JPEG, PNG и GIF изображения')
            
            # Получаем расширение файла
            ext = os.path.splitext(avatar.name)[1].lower()
            if not ext:
                ext = '.jpg'  # расширение по умолчанию
            
            # Генерируем уникальное имя на основе username пользователя и текущего времени
            username = self.instance.user.username if self.instance and self.instance.user else 'unknown'
            unique_string = f"{username}_{timezone.now().timestamp()}"
            hash_name = hashlib.md5(unique_string.encode()).hexdigest() + ext
            
            # Переименовываем файл
            avatar.name = hash_name
        
        return avatar


class CustomPasswordChangeForm(PasswordChangeForm):
    """Кастомная форма смены пароля"""
    
    old_password = forms.CharField(
        label='Старый пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Введите старый пароль'})
    )
    
    new_password1 = forms.CharField(
        label='Новый пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Введите новый пароль'}),
        help_text='Минимум 8 символов.'
    )
    
    new_password2 = forms.CharField(
        label='Подтверждение нового пароля',
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Повторите новый пароль'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].widget.attrs['class'] = 'form-input'
    
    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1')
        if password and len(password) < 8:
            raise forms.ValidationError('Пароль должен содержать минимум 8 символов.')
        return password