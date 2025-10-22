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
from django.template.loader import render_to_string
from django.http import JsonResponse


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
    model = Article
    template_name = 'news/article_list.html' 
    context_object_name = 'articles'
    # --- UBAH INI JADI 9 ---
    paginate_by = 9 

    def get_queryset(self):
        queryset = super().get_queryset().order_by('-created_at') # Selalu urutkan terbaru
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Article.CATEGORY_CHOICES
        context['current_category'] = self.request.GET.get('category')
        return context

    # --- TAMBAHKAN ATAU MODIFIKASI METHOD GET INI ---
    def get(self, request, *args, **kwargs):
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('ajax') == 'true'

        if is_ajax:

            self.object_list = self.get_queryset()

            paginator = self.get_paginator(self.object_list, self.paginate_by)
            page_obj = paginator.get_page(1)
            
            context = {
                'articles': page_obj.object_list,
                'page_obj': page_obj, 
                'is_paginated': page_obj.has_other_pages(),

            }

            html = render_to_string(
                'news/_article_grid_partial.html',
                context,
                request=request
            )
            # Kirim HTML sebagai JSON response
            return JsonResponse({'html': html})
        else:
            # Jika BUKAN AJAX, lanjutkan seperti biasa (render halaman penuh)
            return super().get(request, *args, **kwargs)


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