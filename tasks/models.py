from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify
from simple_history.models import HistoricalRecords
from directories.models import Record

class Task(models.Model):
    title = models.CharField('Название', max_length=200, blank=False)
    description = models.TextField('Описание', blank=True)
    task_type = models.ForeignKey(
        Record, on_delete=models.SET_NULL, null=True,
        limit_choices_to={'directory__slug': 'task_types', 'is_deleted': False},
        verbose_name='Тип задачи',
        related_name='tasks_as_type'
    )
    status = models.ForeignKey(
        Record, on_delete=models.SET_NULL, null=True,
        limit_choices_to={'directory__slug': 'task_statuses', 'is_deleted': False},
        verbose_name='Статус',
        related_name='tasks_as_status'
    )
    priority = models.ForeignKey(
        Record, on_delete=models.SET_NULL, null=True,
        limit_choices_to={'directory__slug': 'task_priorities', 'is_deleted': False},
        verbose_name='Приоритет',
        related_name='tasks_as_priority'
    )
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='authored_tasks', verbose_name='Автор')
    assignee = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_tasks', verbose_name='Исполнитель'
    )
    created_at = models.DateTimeField('Создана', auto_now_add=True)
    deadline = models.DateTimeField('Дедлайн', null=True, blank=True)
    completed_at = models.DateTimeField('Завершена', null=True, blank=True)
    estimated_hours = models.DecimalField('План (часы)', max_digits=5, decimal_places=1, null=True, blank=True)
    actual_hours = models.DecimalField('Факт (часы)', max_digits=5, decimal_places=1, null=True, blank=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True, verbose_name='Slug')

    # Версионность
    history = HistoricalRecords()

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Сначала сохраняем объект, если его ещё нет (чтобы получить pk)
        if not self.pk and not self.slug:
            super().save(*args, **kwargs)   # сохраняем без slug
            # Теперь у нас есть id, генерируем slug
            base_slug = slugify(self.title) if self.title else f"task-{self.pk}"
            if not base_slug:
                base_slug = f"task-{self.pk}"
            slug = base_slug
            counter = 1
            while Task.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
            # Сохраняем снова, обновляя slug
            super().save(update_fields=['slug'])
        else:
            # Для существующих объектов, если slug пуст (например, старые данные)
            if not self.slug:
                base_slug = slugify(self.title) if self.title else f"task-{self.pk}"
                if not base_slug:
                    base_slug = f"task-{self.pk}"
                slug = base_slug
                counter = 1
                while Task.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                self.slug = slug
            super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('tasks:task_detail', args=[self.slug])

    @property
    def total_votes(self):
        return self.votes.aggregate(total=models.Sum('value'))['total'] or 0
    
    @property
    def type_display(self):
        """Название типа задачи (из справочника)"""
        if self.task_type:
            # Ищем первое текстовое поле (string или text) у записи справочника
            text_value = self.task_type.values.filter(field__field_type__in=['string', 'text']).first()
            return text_value.value if text_value else str(self.task_type)
        return '—'

    @property
    def status_display(self):
        if self.status:
            text_value = self.status.values.filter(field__field_type__in=['string', 'text']).first()
            return text_value.value if text_value else str(self.status)
        return '—'

    @property
    def priority_display(self):
        if self.priority:
            text_value = self.priority.values.filter(field__field_type__in=['string', 'text']).first()
            return text_value.value if text_value else str(self.priority)
        return '—'


class TaskVote(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='votes', verbose_name='Задача')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    value = models.SmallIntegerField(default=1, verbose_name='Голос (+1/-1)')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('task', 'user')
        verbose_name = 'Голос'
        verbose_name_plural = 'Голоса'

    def __str__(self):
        return f'{self.user.username} → {self.task.title}: {self.value}'


class TaskComment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments', verbose_name='Задача')
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Автор')
    text = models.TextField('Текст комментария')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return f'{self.author} - {self.task.title[:20]}'