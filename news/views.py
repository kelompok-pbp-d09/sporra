
from django.shortcuts import render, get_object_or_404
from .models import Article, Category

def article_list(request):
    # Get all articles
    articles = Article.objects.all()
    
    # Get all categories for the filter dropdown/links
    categories = Category.objects.all()

    # Filter logic
    category_slug = request.GET.get('category')
    if category_slug:
        # Filter articles by the selected category slug
        category = get_object_or_404(Category, slug=category_slug)
        articles = articles.filter(category=category)

    context = {
        'articles': articles,
        'categories': categories,
        'selected_category': category_slug, # To show which filter is active
    }
    return render(request, 'news/article_list.html', context)


def article_detail(request, slug):
    article = get_object_or_404(Article, slug=slug)
    context = {
        'article': article,
    }
    return render(request, 'news/article_detail.html', context)