from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import Task, TaskVote, TaskComment

@admin.register(Task)
class TaskAdmin(SimpleHistoryAdmin):
    list_display = ('title', 'status', 'priority', 'assignee', 'author', 'total_votes')
    list_filter = ('status', 'priority', 'task_type')
    search_fields = ('title', 'description')
    readonly_fields = ('slug', 'created_at', 'total_votes')

@admin.register(TaskVote)
class TaskVoteAdmin(admin.ModelAdmin):
    list_display = ('task', 'user', 'value', 'created_at')
    list_filter = ('value',)

@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ('task', 'author', 'created_at')
    list_filter = ('created_at',)