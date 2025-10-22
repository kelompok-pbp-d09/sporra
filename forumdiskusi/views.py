from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import ForumDiskusi, Post
from news.models import News


# Semua orang (termasuk yang belum login) bisa lihat forum
def forum(request, news_id):
    forum, created = ForumDiskusi.objects.get_or_create(news_id=news_id)
    comments = forum.posts.all().order_by('-created_at')

    context = {
        'forum': forum,
        'news': forum.news,
        'comments': comments,
    }
    return render(request, 'forum.html', context)


# Hanya user login yang boleh nambah komentar
@login_required
def add_comment(request, news_id):
    if request.method == 'POST':
        forum, _ = ForumDiskusi.objects.get_or_create(news_id=news_id)
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


# Hanya penulis komentar atau admin yang boleh hapus
@login_required
def delete_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    user = request.user
    is_admin = hasattr(user, 'userprofile') and user.userprofile.is_admin

    if post.author == user or is_admin:
        post.delete()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect('forumdiskusi:forum', news_id=post.forum.news.id)

    return JsonResponse({'error': 'Tidak memiliki izin untuk menghapus'}, status=403)