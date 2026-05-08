from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.core.paginator import Paginator
from directories.models import Record
from .models import Task, TaskVote, TaskComment
from .forms import TaskForm, TaskCommentForm

#количества записей пагинатора
PAGINATE_BY = 10

def get_filter_lists():
    """Возвращает словарь с записями справочников для правого меню, отсортированными по позиции."""
    return {
        'task_types': Record.objects.filter(
            directory__slug='task_types', is_deleted=False
        ).order_by('-position', 'id'),
        'task_priorities': Record.objects.filter(
            directory__slug='task_priorities', is_deleted=False
        ).order_by('-position', 'id'),
        'task_statuses': Record.objects.filter(
            directory__slug='task_statuses', is_deleted=False
        ).order_by('-position', 'id'),
    }

def _paginate_tasks(request, tasks_queryset_or_list):
    # tasks_queryset_or_list должен быть отсортированным списком
    paginator = Paginator(tasks_queryset_or_list, PAGINATE_BY)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)

def task_list(request):
    # Исключаем статусы "Завершена" и "Отклонена" по названию (значению текстового поля)
    excluded_names = ['Завершена', 'Отклонена']
    excluded_statuses = Record.objects.filter(
        directory__slug='task_statuses',
        values__value__in=excluded_names,
        values__field__field_type__in=['string', 'text'],
        is_deleted=False
    ).values_list('id', flat=True)

    tasks = Task.objects.exclude(status_id__in=excluded_statuses)
    
    # Сортировка по голосам
    tasks = sorted(tasks, key=lambda t: t.total_votes, reverse=True)

    page_obj = _paginate_tasks(request, tasks)
    return render(request, 'tasks/task_list.html', {
        'page_obj': page_obj,
        'filter_lists': get_filter_lists(),
        'active_filter': None,
        'show_all': False,
    })


def task_list_all(request):
    """Все задачи без исключений."""
    tasks = Task.objects.all()
    tasks = sorted(tasks, key=lambda t: t.total_votes, reverse=True)
    page_obj = _paginate_tasks(request, tasks)
    return render(request, 'tasks/task_list.html', {
        'page_obj': page_obj,
        'filter_lists': get_filter_lists(),
        'active_filter': None,
        'show_all': True,
    })

def task_list_filtered(request, slug):
    """Фильтр по slug: сначала ищем среди типов, затем приоритетов, затем статусов."""
    record = None
    filter_type = None  # 'task_type', 'priority' или 'status'
    # Поиск в типах
    rec = Record.objects.filter(directory__slug='task_types', slug=slug, is_deleted=False).first()
    if rec:
        record = rec
        filter_type = 'task_type'
    else:
        rec = Record.objects.filter(directory__slug='task_priorities', slug=slug, is_deleted=False).first()
        if rec:
            record = rec
            filter_type = 'priority'
        else:
            rec = Record.objects.filter(directory__slug='task_statuses', slug=slug, is_deleted=False).first()
            if rec:
                record = rec
                filter_type = 'status'

    if not record:
        raise Http404("Запись не найдена в справочниках типов, приоритетов или статусов")

    tasks = Task.objects.filter(**{filter_type: record})
    tasks = sorted(tasks, key=lambda t: t.total_votes, reverse=True)
    page_obj = _paginate_tasks(request, tasks)

    return render(request, 'tasks/task_list.html', {
        'page_obj': page_obj,
        'filter_lists': get_filter_lists(),
        'active_filter': {
            'type': filter_type,
            'slug': slug,
            'record': record,
            'display_name': record.get_display_name(),
        },
        'show_all': False,
    })

# ---- CRUD для задач (с использованием PK) ----
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk)
    comment_form = TaskCommentForm()
    user_vote = None
    if request.user.is_authenticated:
        user_vote = TaskVote.objects.filter(task=task, user=request.user).first()
    return render(request, 'tasks/task_detail.html', {
        'task': task,
        'comment_form': comment_form,
        'user_vote': user_vote,
        'filter_lists': get_filter_lists(),
    })

@login_required
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.author = request.user
            task.save()
            messages.success(request, f'Задача "{task.title}" создана.')
            #return redirect('tasks:task_detail', pk=task.pk) # Возврат после создания на страницу созданной задачи
            return redirect('tasks:task_list') # Возврат после создания на главную страницу приложения
    else:
        form = TaskForm()
    return render(request, 'tasks/task_form.html', {
        'form': form,
        'title': 'Создать задачу',
        'filter_lists': get_filter_lists(),
    })

@login_required
def task_edit(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if task.author != request.user and not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, 'Вы не можете редактировать эту задачу.')
        return redirect('tasks:task_detail', pk=task.pk)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Задача обновлена.')
            return redirect('tasks:task_detail', pk=task.pk)
    else:
        form = TaskForm(instance=task)
    return render(request, 'tasks/task_form.html', {
        'form': form,
        'title': 'Редактировать задачу',
        'filter_lists': get_filter_lists(),
    })

@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if task.author != request.user and not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, 'Вы не можете удалить эту задачу.')
        return redirect('tasks:task_detail', pk=task.pk)
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Задача удалена.')
        return redirect('tasks:task_list')
    return render(request, 'tasks/task_confirm_delete.html', {
        'task': task,
        'filter_lists': get_filter_lists(),
    })

@login_required
def task_vote(request, pk):
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не разрешён'}, status=405)
    task = get_object_or_404(Task, pk=pk)
    direction = request.POST.get('direction')
    if direction not in ('up', 'down'):
        return JsonResponse({'error': 'Неверное направление'}, status=400)

    vote_value = 1 if direction == 'up' else -1
    vote, created = TaskVote.objects.get_or_create(task=task, user=request.user)
    if not created and vote.value == vote_value:
        vote.delete()
        new_total = task.total_votes
        return JsonResponse({'status': 'removed', 'total_votes': new_total})
    else:
        vote.value = vote_value
        vote.save()
        new_total = task.total_votes
        return JsonResponse({'status': 'voted', 'total_votes': new_total})

@login_required
def task_resolve(request, pk):
    task = get_object_or_404(Task, pk=pk)
    # Проверка прав: только автор или администратор
    if task.author != request.user and not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, 'Вы не можете отметить эту задачу как решённую.')
        return redirect('tasks:task_detail', pk=task.pk)

    # Находим статус "Завершена" (по slug 'completed' или по названию)
    completed_status = Record.objects.filter(
        directory__slug='task_statuses',
        slug='completed'  # если slug не задан, используйте values__value='Завершена'
    ).first()
    if not completed_status:
        # fallback: ищем по названию
        completed_status = Record.objects.filter(
            directory__slug='task_statuses',
            values__value='Завершена',
            values__field__field_type__in=['string', 'text']
        ).first()
    if completed_status:
        task.status = completed_status
        task.save()
        messages.success(request, f'Задача "{task.title}" отмечена как решённая.')
    else:
        messages.error(request, 'Не найден статус "Завершена". Обратитесь к администратору.')

    return redirect('tasks:task_list')   # редирект на список задач    

def task_history(request, pk):
    task = get_object_or_404(Task, pk=pk)
    history_list = task.history.all().order_by('-history_date')
    return render(request, 'tasks/task_history.html', {
        'task': task,
        'history_list': history_list,
        'filter_lists': get_filter_lists(),
    })

def task_comments(request, pk):
    task = get_object_or_404(Task, pk=pk)
    comments = task.comments.all()
    if request.method == 'POST' and request.user.is_authenticated:
        form = TaskCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.task = task
            comment.author = request.user
            comment.save()
            messages.success(request, 'Комментарий добавлен.')
            return redirect('tasks:task_comments', pk=task.pk)
    else:
        form = TaskCommentForm()
    return render(request, 'tasks/task_comments.html', {
        'task': task,
        'comments': comments,
        'form': form,
        'filter_lists': get_filter_lists(),
    })