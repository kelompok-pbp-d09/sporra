from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Sum
from .models import ForumDiskusi, Post, Vote
from news.models import Article

# Forum bisa diakses tanpa login
def forum(request, pk):
    article = get_object_or_404(Article, pk=pk)
    forum, created = ForumDiskusi.objects.get_or_create(article=article)
    comments = forum.posts.all().order_by('-score', '-created_at')

    # Ambil status vote user (biar tau udah upvote/downvote belum)
    user_votes = {}
    if request.user.is_authenticated:
        votes = Vote.objects.filter(user=request.user, post__in=comments)
        user_votes = {v.post.id: v.value for v in votes}

    context = {
        'forum': forum,
        'news': article,
        'comments': comments,
        'user_votes': user_votes,
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


@login_required
def vote_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    vote_type = request.POST.get('vote')  # 'up' atau 'down'

    if vote_type not in ['up', 'down']:
        return JsonResponse({'error': 'Vote tidak valid'}, status=400)

    value = 1 if vote_type == 'up' else -1

    # Tambahkan defaults biar gak error NULL
    vote, created = Vote.objects.get_or_create(
        post=post,
        user=request.user,
        defaults={'value': value}
    )

    if not created and vote.value == value:
        # Klik ulang arah yang sama → hapus vote (unvote)
        vote.delete()
        user_vote = None
    else:
        # Baru atau ubah arah vote
        vote.value = value
        vote.save()
        user_vote = vote_type

    # Hitung ulang skor
    total = post.votes.aggregate(total=Sum('value'))['total'] or 0
    post.score = total
    post.save()

    return JsonResponse({
        'score': total,
        'user_vote': user_vote,
    })


def preview(request):
    """Preview forum tanpa data real (dummy mode)"""
    from django.contrib.auth.models import User

    article = Article(
        id='00000000-0000-0000-0000-000000000000',
        title='Contoh Berita untuk Preview',
        content='Ini adalah artikel contoh untuk melihat tampilan forum diskusi.'
    )

    dummy_user = User(username='tester')
    forum = ForumDiskusi(article=article)
    comments = [
        Post(id=1, author=dummy_user, content='Komentar contoh pertama', created_at='2025-10-23 10:00'),
        Post(id=2, author=dummy_user, content='Komentar contoh kedua', created_at='2025-10-23 11:00'),
    ]

    context = {
        'forum': forum,
        'news': article,
        'comments': comments,
    }
    return render(request, 'forum.html', context)
