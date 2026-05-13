from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget
from .models import PhotoAlbum, Photo

class PhotoAlbumForm(forms.ModelForm):
    class Meta:
        model = PhotoAlbum
        fields = ['title', 'description', 'author', 'source', 'privacy', 'allow_downloads', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            #'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 4}),
            'description': CKEditor5Widget(config_name='default', attrs={'class': 'form-input django_ckeditor_5'}),
            'author': forms.TextInput(attrs={'class': 'form-input'}),
            'source': forms.URLInput(attrs={'class': 'form-input'}),
            'privacy': forms.Select(attrs={'class': 'form-input'}),
            'allow_downloads': forms.CheckboxInput(attrs={'class': 'form-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-input'}),
        }

class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ['alt_text', 'position', 'is_favorite', 'author', 'source']
        widgets = {
            'alt_text': forms.TextInput(attrs={'class': 'form-input'}),
            'position': forms.NumberInput(attrs={'class': 'form-input'}),
            'is_favorite': forms.CheckboxInput(attrs={'class': 'form-input'}),
            'author': forms.TextInput(attrs={'class': 'form-input'}),
            'source': forms.URLInput(attrs={'class': 'form-input'}),
        }