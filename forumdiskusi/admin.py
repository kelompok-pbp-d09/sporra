from django.contrib import admin
from .models import ForumDiskusi, Post, Vote

@admin.register(ForumDiskusi)
class ForumDiskusiAdmin(admin.ModelAdmin):
    list_display = ('id', 'article', 'created_at')
    search_fields = ('article__title',)
    readonly_fields = ('article', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'forum', 'author', 'created_at', 'score')
    search_fields = ('author__username', 'content')
    readonly_fields = ('forum', 'author', 'content', 'created_at', 'score')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'user', 'value')
    search_fields = ('user__username', 'post__content')
    readonly_fields = ('post', 'user', 'value')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
