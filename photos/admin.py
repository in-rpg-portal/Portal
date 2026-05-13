from django.contrib import admin
from django import forms
from .models import PhotoAlbum, Photo

class PhotoAlbumForm(forms.ModelForm):
    class Meta:
        model = PhotoAlbum
        fields = ['title', 'description', 'author', 'source', 'privacy', 'allow_downloads', 'order', 'owner']  # owner добавлен

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Если это создание нового объекта (нет instance.pk), то подставляем текущего пользователя
        if not self.instance.pk:
            # Получить request можно только через внешний параметр, но в админке проще через save_model
            # Здесь мы не имеем доступа к request, поэтому initial установим в save_model.
            pass

class PhotoAdminForm(forms.ModelForm):
    image = forms.ImageField(label='Изображение', required=True)
    class Meta:
        model = Photo
        fields = ['album', 'image', 'original_name', 'alt_text', 'position', 'is_favorite', 'uploaded_by', 'author', 'source', 'metadata']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['original_name'].disabled = True
        #self.fields['uploaded_by'].disabled = True

    def save(self, commit=True):
        photo = super().save(commit=False)
        photo._file = self.cleaned_data['image']
        if commit:
            photo.save()
        return photo


@admin.register(PhotoAlbum)
class PhotoAlbumAdmin(admin.ModelAdmin):
    form = PhotoAlbumForm
    list_display = ('title', 'owner', 'privacy', 'is_deleted', 'created_at')
    list_filter = ('privacy', 'is_deleted')
    search_fields = ('title', 'description')

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # При создании нового альбома (obj is None) устанавливаем начальное значение owner = request.user
        if obj is None:
            form.base_fields['owner'].initial = request.user
        return form

    def save_model(self, request, obj, form, change):
        # Если объект новый и owner не установлен (на всякий случай), ставим текущего пользователя
        if not obj.pk and not obj.owner:
            obj.owner = request.user
        super().save_model(request, obj, form, change)


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    form = PhotoAdminForm
    list_display = ('id', 'album', 'original_name', 'uploaded_by', 'uploaded_at', 'position', 'is_deleted')
    list_filter = ('is_deleted',)
    readonly_fields = ('uploaded_at',)

    def save_model(self, request, obj, form, change):
        if not obj.pk and not obj.uploaded_by:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)