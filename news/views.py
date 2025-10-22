from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import (
    ListView, 
    DetailView, 
    CreateView, 
    UpdateView, 
    DeleteView,
    TemplateView,
)
# For security: only logged-in users can create/edit/delete
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Article


# --- View Landing page ---
class LandingPageView(TemplateView):
    """
    View untuk menampilkan landing page utama di root '/'.
    """
    template_name = 'landing.html'
    
    # --- LOGIKA UNTUK 'hottest_articles' HARUSNYA ADA DI SINI ---
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Mengambil 3 artikel TERBARU (lebih baik untuk situs baru)
        context['hottest_articles'] = Article.objects.order_by('-created_at')[:3]
        return context


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
    
    def get_context_data(self, **kwargs):
        # 1. Panggil implementasi super()
        context = super().get_context_data(**kwargs)
        
        # 2. Ambil data artikel
        # Kita ambil 3 artikel, diurutkan dari views terbanyak
        context['hottest_articles'] = Article.objects.order_by('-news_views')[:3]
        
        # 3. Kirim kembali context-nya
        return context

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
            # Panggil implementasi super() dulu
            context = super().get_context_data(**kwargs)
            
            # Tambahkan data untuk filter kategori
            context['categories'] = Article.CATEGORY_CHOICES
            context['current_category'] = self.request.GET.get('category')
            
            # (Logika 'hottest_articles' sudah DIHAPUS dari sini)
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