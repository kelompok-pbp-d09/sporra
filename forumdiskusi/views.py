from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import ForumDiskusi, Post
from news.models import Article

# Forum bisa diakses tanpa login
def forum(request, pk):
    article = get_object_or_404(Article, pk=pk)
    forum, created = ForumDiskusi.objects.get_or_create(article=article)
    comments = forum.posts.all().order_by('-created_at')

    context = {
        'forum': forum,
        'news': article,
        'comments': comments,
    }
    return render(request, 'forum.html', context)


@login_required
def add_comment(request, pk):
    article = get_object_or_404(Article, pk=pk)
    forum, _ = ForumDiskusi.objects.get_or_create(article=article)

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if not content:
            return JsonResponse({'error': 'Isi komentar tidak boleh kosong'}, status=400)

        post = Post.objects.create(
            forum=forum,
            author=request.user,
            content=content
        )

        return JsonResponse({
            'id': post.id,
            'username': post.author.username,
            'content': post.content,
            'created_at': post.created_at.strftime("%d %b %Y, %H:%M"),
        })

    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def delete_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    user = request.user
    is_admin = hasattr(user, 'userprofile') and user.userprofile.is_admin

    if post.author == user or is_admin:
        post.delete()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect('forumdiskusi:forum', pk=post.forum.article.pk)

    return JsonResponse({'error': 'Tidak memiliki izin untuk menghapus'}, status=403)
