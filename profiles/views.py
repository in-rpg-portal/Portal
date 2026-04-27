from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from .forms import SignUpForm, ProfileEditForm
from .models import Profile

def signup(request):
    """Регистрация нового пользователя"""
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Автоматически входим после регистрации
            login(request, user)
            return redirect('profiles:profile_detail', pk=user.profile.pk)
    else:
        form = SignUpForm()
    
    return render(request, 'profiles/signup.html', {'form': form})

def profile_detail(request, pk):
    """Просмотр профиля пользователя"""
    profile = get_object_or_404(Profile, pk=pk)
    return render(request, 'profiles/profile_detail.html', {'profile': profile})

@login_required
def profile_edit(request):
    """Редактирование своего профиля"""
    profile = request.user.profile
    
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profiles:profile_detail', pk=profile.pk)
    else:
        form = ProfileEditForm(instance=profile)
    
    return render(request, 'profiles/profile_edit.html', {'form': form, 'profile': profile})

def about(request):
    """Страница о проекте"""
    return render(request, 'profiles/about.html')