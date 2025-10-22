from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import (
    ListView, 
    DetailView, 
    CreateView, 
    UpdateView, 
    DeleteView
)
# For security: only logged-in users can create/edit/delete
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Article

# --- READ Views ---

class ArticleListView(ListView):
    """
    Shows a list of all articles.
    Also handles filtering by category based on a URL query parameter.
    e.g., /articles?category=f1
    """
    model = Article
    template_name = 'news/article_list.html'  # You need to create this template
    context_object_name = 'articles'
    paginate_by = 10  # Shows 10 articles per page

    def get_queryset(self):
        # Start with all articles
        queryset = super().get_queryset()
        
        # Get the category from the URL (e.g., ?category=sepakbola)
        category = self.request.GET.get('category')
        
        if category:
            # If a category is provided, filter the queryset
            queryset = queryset.filter(category=category)
            
        return queryset

    def get_context_data(self, **kwargs):
        # This adds the list of categories to the context
        # so you can build filter links in your template
        context = super().get_context_data(**kwargs)
        context['categories'] = Article.CATEGORY_CHOICES
        context['current_category'] = self.request.GET.get('category')
        return context


class ArticleDetailView(DetailView):
    """
    Shows a single article.
    This view also increments the 'news_views' count.
    """
    model = Article
    template_name = 'news/article_detail.html' # You need to create this template
    context_object_name = 'article'

    def get_object(self, queryset=None):
        # Get the article object
        article = super().get_object(queryset)
        
        # Call the model's method to increment its view count
        # This happens every time the detail page is loaded
        article.increment_views()
        
        return article

# --- CREATE View ---

class ArticleCreateView(LoginRequiredMixin, CreateView):
    """
    A form for creating a new article.
    Only logged-in users can access this.
    """
    model = Article
    template_name = 'news/article_form.html' # You need to create this
    fields = ['title', 'content', 'thumbnail', 'category'] # Fields user can fill
    
    def form_valid(self, form):
        # Automatically set the author to the currently logged-in user
        form.instance.author = self.request.user
        return super().form_valid(form)


# --- UPDATE View ---

class ArticleUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    A form for updating an existing article.
    Only the *original author* can update it.
    """
    model = Article
    template_name = 'news/article_form.html' # Can reuse the create form
    fields = ['title', 'content', 'thumbnail', 'category']

    def test_func(self):
        # This test ensures only the author can edit
        article = self.get_object()
        return self.request.user == article.author


# --- DELETE View ---

class ArticleDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    A confirmation page for deleting an article.
    Only the *original author* can delete it.
    """
    model = Article
    template_name = 'news/article_confirm_delete.html' # You need to create this
    success_url = reverse_lazy('news:article-list') # Redirect to list after delete

    def test_func(self):
        # This test ensures only the author can delete
        article = self.get_object()
        return self.request.user == article.author