from django.urls import path
from django.shortcuts import render

def home(request):
    return render(request, 'base.html')

urlpatterns = [
    path('', home, name='home'),
]