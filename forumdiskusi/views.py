from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Sum, Count
from .models import ForumDiskusi, Post, Vote
from news.models import Article


def forum(request, pk):
    article = get_object_or_404(Article, pk=pk)
    forum, created = ForumDiskusi.objects.get_or_create(article=article)
    comments = forum.posts.all().order_by('-score', '-created_at')

    user_votes = {}
    if request.user.is_authenticated:
        votes = Vote.objects.filter(user=request.user, post__in=comments)
        user_votes = {v.post.id: v.value for v in votes}  # simpan nilai numerik

    hottest_articles = (
        Article.objects.exclude(pk=article.pk)  # jangan tampilkan artikel yang sedang dibuka
        .order_by('-news_views')[:6]  # atau '-created_at' jika tidak ada views
    )

    for comment in comments:
        comment.user_vote = user_votes.get(comment.id, 0)  # default 0

    context = {
        'forum': forum,
        'news': article,
        'comments': comments,
        'hottest_articles': hottest_articles,
    }
    return render(request, 'forum.html', context)

from django.utils.timezone import localtime

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

        # ubah ke waktu lokal sebelum dikirim ke frontend
        created_local = localtime(post.created_at)
        # Increment komentar_created counter di UserProfile
        user_profile = request.user.userprofile
        user_profile.increment_komentar()

        return JsonResponse({
            'id': post.id,
            'username': post.author.username,
            'content': post.content,
            'created_at': created_local.strftime("%d %b %Y, %H:%M"),
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
def edit_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    user = request.user
    is_admin = hasattr(user, 'userprofile') and user.userprofile.is_admin

    if post.author != user and not is_admin:
        return JsonResponse({'error': 'Tidak memiliki izin untuk mengedit'}, status=403)

    if request.method == 'POST':
        new_content = request.POST.get('content', '').strip()
        if not new_content:
            return JsonResponse({'error': 'Isi komentar tidak boleh kosong'}, status=400)

        post.content = new_content
        post.save()

        return JsonResponse({'success': True, 'new_content': post.content})

    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def vote_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    vote_type = request.POST.get('vote')  # 'up' atau 'down'

    if vote_type not in ['up', 'down']:
        return JsonResponse({'error': 'Vote tidak valid'}, status=400)

    value = 1 if vote_type == 'up' else -1

    try:
        vote = Vote.objects.get(post=post, user=request.user)
        # kalau user klik tombol yang sama, maka unvote
        if vote.value == value:
            vote.delete()
            user_vote = 0
        else:
            # kalau user klik arah berlawanan, maka hapus dulu (unvote)
            vote.delete()
            user_vote = 0
    except Vote.DoesNotExist:
        # user belum pernah vote, buat baru
        Vote.objects.create(post=post, user=request.user, value=value)
        user_vote = value

    total = post.votes.aggregate(total=Sum('value'))['total'] or 0
    post.score = total
    post.save()

    return JsonResponse({
        'score': total,
        'user_vote': user_vote,
    })

