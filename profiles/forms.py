from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile

class SignUpForm(UserCreationForm):
    """Форма регистрации нового пользователя"""
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-input'})
    )
    bio = forms.CharField(
        label='О себе',
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-input', 'rows': 4})
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем CSS классы к полям
        for field_name in self.fields:
            if field_name != 'bio':
                self.fields[field_name].widget.attrs['class'] = 'form-input'
        self.fields['username'].widget.attrs['placeholder'] = 'Введите имя пользователя'
        self.fields['email'].widget.attrs['placeholder'] = 'user@example.com'
        self.fields['password1'].widget.attrs['placeholder'] = 'Введите пароль'
        self.fields['password2'].widget.attrs['placeholder'] = 'Повторите пароль'
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Сохраняем bio в профиль
            profile = user.profile
            profile.bio = self.cleaned_data['bio']
            profile.save()
        return user

class ProfileEditForm(forms.ModelForm):
    """Форма редактирования профиля"""
    class Meta:
        model = Profile
        fields = ('bio',)
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-input', 'rows': 6, 'placeholder': 'Расскажите о себе...'}),
        }
        labels = {
            'bio': 'О себе',
        }