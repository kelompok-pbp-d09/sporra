from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse 
from django.db.models import Sum, Count
from django.core import serializers
import json
from .models import ForumDiskusi, Post, Vote
from news.models import Article
import requests
from django.utils.timezone import localtime
from django.views.decorators.csrf import csrf_exempt

def forum(request, pk):
    article = get_object_or_404(Article, pk=pk)
    forum, created = ForumDiskusi.objects.get_or_create(article=article)
    comments = (
        forum.posts.all()
        .order_by('-score', '-created_at')
    )

    top_forums = (
        ForumDiskusi.objects
        .annotate(post_count=Count('posts'))
        .filter(post_count__gt=0)
        .select_related('article')
        .order_by('-post_count')[:3]
    )

    user_votes = {}
    if request.user.is_authenticated:
        votes = Vote.objects.filter(user=request.user, post__in=comments)
        user_votes = {v.post.id: v.value for v in votes}

    hottest_articles = (
        Article.objects.exclude(pk=article.pk)
        .order_by('-news_views')[:3]
    )

    for comment in comments:
        comment.user_vote = user_votes.get(comment.id, 0)

    context = {
        'forum': forum,
        'news': article,
        'comments': comments,
        'hottest_articles': hottest_articles,
        'top_forums': top_forums,
    }
    return render(request, 'forum.html', context)

@csrf_exempt
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
        created_local = localtime(post.created_at)

        return JsonResponse({
            'id': post.id,
            'username': post.author.username,
            'content': post.content,
            'created_at': created_local.strftime("%d %b %Y, %H:%M"),
        })

    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
@login_required
def delete_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    user = request.user
    is_admin = hasattr(user, 'userprofile') and user.userprofile.is_admin

    if post.author == user or is_admin:
        post.delete()
        return JsonResponse({'success': True})

    return JsonResponse({'error': 'Tidak memiliki izin untuk menghapus'}, status=403)

@csrf_exempt
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

@csrf_exempt
@login_required
def vote_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    vote_type = request.POST.get('vote')

    if vote_type not in ['up', 'down']:
        return JsonResponse({'error': 'Vote tidak valid'}, status=400)

    value = 1 if vote_type == 'up' else -1

    try:
        vote = Vote.objects.get(post=post, user=request.user)

        # Jika klik vote yang sama → hapus → netral
        if vote.value == value:
            vote.delete()
            user_vote = 0

        # Jika klik vote berbeda → tetap netral (sesuai keinginanmu)
        else:
            vote.delete()
            user_vote = 0

    except Vote.DoesNotExist:
        # Belum pernah vote → buat vote baru
        Vote.objects.create(post=post, user=request.user, value=value)
        user_vote = value

    # Hitung total score
    total = post.votes.aggregate(total=Sum('value'))['total'] or 0
    post.score = total
    post.save()

    return JsonResponse({
        'score': total,
        'user_vote': user_vote,
    })


def proxy_image(request):
    image_url = request.GET.get('url')
    if not image_url:
        return HttpResponse('No URL provided', status=400)
    
    try:
        # Fetch image from external source
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        
        # Return the image with proper content type
        return HttpResponse(
            response.content,
            content_type=response.headers.get('Content-Type', 'image/jpeg')
        )
    except requests.RequestException as e:
        return HttpResponse(f'Error fetching image: {str(e)}', status=500)

def forum_json(request, pk):
    article = get_object_or_404(Article, pk=pk)
    forum, _ = ForumDiskusi.objects.get_or_create(article=article)
    comments = forum.posts.all().order_by('-score', '-created_at')

    def news_entry_format(a):
        return {
            "model": "news.article",
            "pk": str(a.pk),
            "fields": {
                "title": a.title,
                "content": a.content,
                "category": a.category,
                "thumbnail": a.thumbnail or "",
                "news_views": a.news_views,
                "created_at": a.created_at.isoformat(),
                "author": a.author.username if a.author else "",
            }
        }

    top_forums_qs = (
        ForumDiskusi.objects
        .annotate(post_count=Count('posts'))
        .filter(post_count__gt=0)
        .select_related('article')
        .order_by('-post_count')[:3]
    )

    top_forums_json = [
        {
            "post_count": tf.post_count,
            "article": news_entry_format(tf.article)
        }
        for tf in top_forums_qs
    ]


    # Hottest articles
    hottest_articles = Article.objects.exclude(pk=article.pk).order_by('-news_views')[:3]
    hottest_json = [news_entry_format(h) for h in hottest_articles]

    # Comments + user_vote
    comments_json = []
    for c in comments:
        vote = None
        if request.user.is_authenticated:
            vote = Vote.objects.filter(post=c, user=request.user).first()

        user_vote = vote.value if vote else 0
        pfp_url = ""
        try:
            if hasattr(c.author, 'userprofile'):
                pfp_url = c.author.userprofile.profile_picture or ""
        except Exception:
            pfp_url = ""

        comments_json.append({
            "id": c.id,
            "author": c.author.username,
            "author_pfp": pfp_url,
            "content": c.content,
            "score": c.score,
            "created_at": c.created_at.isoformat(),
            "user_vote": user_vote,
        })

    # FINAL JSON
    return JsonResponse({
        "forum_id": str(forum.id),
        "article": news_entry_format(article),
        "comments": comments_json,
        "top_forums": top_forums_json,
        "hottest_articles": hottest_json,
    })
