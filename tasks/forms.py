from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget
from django.contrib.auth.models import User
from .models import Task, TaskComment
from directories.models import Record

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ('title', 'description', 'task_type', 'status', 'priority',
                  'assignee', 'deadline', 'estimated_hours', 'actual_hours')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'description': CKEditor5Widget(config_name='default', attrs={'class': 'form-input'}),
            'task_type': forms.Select(attrs={'class': 'form-input'}),
            'status': forms.Select(attrs={'class': 'form-input'}),
            'priority': forms.Select(attrs={'class': 'form-input'}),
            'assignee': forms.Select(attrs={'class': 'form-input'}),
            'deadline': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
            'estimated_hours': forms.NumberInput(attrs={'class': 'form-input', 'step': 0.5}),
            'actual_hours': forms.NumberInput(attrs={'class': 'form-input', 'step': 0.5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Убираем пустой пункт изначально (для всех)
        self.fields['task_type'].empty_label = None
        self.fields['status'].empty_label = None
        self.fields['priority'].empty_label = None

        # Ограничиваем выбор записей из соответствующих справочников
        self.fields['task_type'].queryset = Record.objects.filter(directory__slug='task_types', is_deleted=False)
        self.fields['status'].queryset = Record.objects.filter(directory__slug='task_statuses', is_deleted=False)
        self.fields['priority'].queryset = Record.objects.filter(directory__slug='task_priorities', is_deleted=False)
        self.fields['assignee'].queryset = User.objects.filter(is_active=True)

        # Если создаётся новая задача
        if not self.instance.pk:
            # Тип задачи
            default_type = Record.objects.filter(directory__slug='task_types', is_default=True, is_deleted=False).first()
            if default_type:
                self.initial['task_type'] = default_type.pk
            else:
                self.fields['task_type'].empty_label = '---------'
            # Статус
            default_status = Record.objects.filter(directory__slug='task_statuses', is_default=True, is_deleted=False).first()
            if default_status:
                self.initial['status'] = default_status.pk
            else:
                self.fields['status'].empty_label = '---------'
            # Приоритет
            default_priority = Record.objects.filter(directory__slug='task_priorities', is_default=True, is_deleted=False).first()
            if default_priority:
                self.initial['priority'] = default_priority.pk
            else:
                self.fields['priority'].empty_label = '---------'


class TaskCommentForm(forms.ModelForm):
    class Meta:
        model = TaskComment
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Ваш комментарий...'})
        }