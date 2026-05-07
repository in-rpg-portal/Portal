from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import Task, TaskVote, TaskComment
from .forms import TaskForm, TaskCommentForm

def task_list(request):
    tasks = Task.objects.all()
    # Фильтрация (простые фильтры – по GET-параметрам)
    status_slug = request.GET.get('status')
    if status_slug:
        tasks = tasks.filter(status__slug=status_slug)
    type_slug = request.GET.get('type')
    if type_slug:
        tasks = tasks.filter(task_type__slug=type_slug)
    priority_slug = request.GET.get('priority')
    if priority_slug:
        tasks = tasks.filter(priority__slug=priority_slug)
    assignee_id = request.GET.get('assignee')
    if assignee_id:
        tasks = tasks.filter(assignee_id=assignee_id)
    author_id = request.GET.get('author')
    if author_id:
        tasks = tasks.filter(author_id=author_id)

    # Сортировка по голосам
    tasks = sorted(tasks, key=lambda t: t.total_votes, reverse=True)

    # Пагинация
    paginator = Paginator(tasks, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'tasks/task_list.html', {'page_obj': page_obj})


def task_detail(request, slug):
    task = get_object_or_404(Task, slug=slug)
    comment_form = TaskCommentForm()
    user_vote = None
    if request.user.is_authenticated:
        user_vote = TaskVote.objects.filter(task=task, user=request.user).first()
    return render(request, 'tasks/task_detail.html', {
        'task': task,
        'comment_form': comment_form,
        'user_vote': user_vote,
    })


@login_required
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.author = request.user
            task.save()   # внутри save() уже сгенерируется slug
            # Дополнительная проверка на случай, если slug всё ещё пуст
            if not task.slug:
                # Повторно сохраняем, чтобы вызвать генерацию slug (на случай бага)
                task.save()
            messages.success(request, f'Задача "{task.title}" создана.')
            return redirect('tasks:task_detail', slug=task.slug)
    else:
        form = TaskForm()
    return render(request, 'tasks/task_form.html', {'form': form, 'title': 'Создать задачу'})


@login_required
def task_edit(request, slug):
    task = get_object_or_404(Task, slug=slug)
    if task.author != request.user and not request.user.is_superuser:
        messages.error(request, 'Вы не можете редактировать эту задачу.')
        return redirect('tasks:task_detail', slug=task.slug)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Задача обновлена.')
            return redirect('tasks:task_detail', slug=task.slug)
    else:
        form = TaskForm(instance=task)
    return render(request, 'tasks/task_form.html', {'form': form, 'title': 'Редактировать задачу'})


@login_required
def task_delete(request, slug):
    task = get_object_or_404(Task, slug=slug)
    if task.author != request.user and not request.user.is_superuser:
        messages.error(request, 'Вы не можете удалить эту задачу.')
        return redirect('tasks:task_detail', slug=task.slug)
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Задача удалена.')
        return redirect('tasks:task_list')
    return render(request, 'tasks/task_confirm_delete.html', {'task': task})


@login_required
def task_vote(request, slug):
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не разрешён'}, status=405)
    task = get_object_or_404(Task, slug=slug)
    # Нельзя голосовать за свои задачи? Решим, что можно (но обычно – нет)
    # if task.author == request.user:
    #     return JsonResponse({'error': 'Нельзя голосовать за свою задачу'}, status=400)

    direction = request.POST.get('direction')  # 'up' или 'down'
    if direction not in ('up', 'down'):
        return JsonResponse({'error': 'Неверное направление'}, status=400)

    vote_value = 1 if direction == 'up' else -1
    vote, created = TaskVote.objects.get_or_create(task=task, user=request.user)
    if not created and vote.value == vote_value:
        # Если голос уже такой же – отменим (удалим)
        vote.delete()
        new_total = task.total_votes
        return JsonResponse({'status': 'removed', 'total_votes': new_total})
    else:
        vote.value = vote_value
        vote.save()
        new_total = task.total_votes
        return JsonResponse({'status': 'voted', 'total_votes': new_total})


def task_history(request, slug):
    task = get_object_or_404(Task, slug=slug)
    history_list = task.history.all().order_by('-history_date')
    return render(request, 'tasks/task_history.html', {'task': task, 'history_list': history_list})


def task_comments(request, slug):
    task = get_object_or_404(Task, slug=slug)
    comments = task.comments.all()
    if request.method == 'POST' and request.user.is_authenticated:
        form = TaskCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.task = task
            comment.author = request.user
            comment.save()
            messages.success(request, 'Комментарий добавлен.')
            return redirect('tasks:task_comments', slug=task.slug)
    else:
        form = TaskCommentForm()
    return render(request, 'tasks/task_comments.html', {
        'task': task,
        'comments': comments,
        'form': form,
    })