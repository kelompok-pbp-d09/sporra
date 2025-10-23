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
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Article
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin


# --- View Landing page ---
class LandingPageView(TemplateView):
    template_name = 'landing.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hottest_articles'] = Article.objects.order_by('-created_at')[:3]
        return context


# --- READ Views ---

class ArticleListView(ListView):
    model = Article
    template_name = 'news/article_list.html' 
    context_object_name = 'articles'
    paginate_by = 9 

    def get_queryset(self):
        queryset = super().get_queryset().order_by('-created_at')
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
            return JsonResponse({'html': html})
        else:
            return super().get(request, *args, **kwargs)


class ArticleDetailView(DetailView):
    model = Article
    template_name = 'news/article_detail.html'
    context_object_name = 'article'

    def get_object(self, queryset=None):
        article = super().get_object(queryset)
        article.increment_views()
        
        return article

# --- CREATE View ---

class ArticleCreateView(SuccessMessageMixin, LoginRequiredMixin, CreateView):
    model = Article
    template_name = 'news/article_form.html'
    fields = ['title', 'content', 'thumbnail', 'category']
    success_message = "Artikel '%(title)s' berhasil dibuat!"
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)
    
        # Increment news_created counter di UserProfile
        user_profile = self.request.user.userprofile
        user_profile.increment_news()

        return response


# --- UPDATE View ---

class ArticleUpdateView(SuccessMessageMixin, LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Article
    template_name = 'news/article_form.html'
    fields = ['title', 'content', 'thumbnail', 'category']
    success_message = "Artikel '%(title)s' berhasil diperbarui!"

    def form_valid(self, form):
        if form.has_changed():
            self.object = form.save()
            messages.success(self.request, f"Artikel '{self.object.title}' berhasil diperbarui!")

            return HttpResponseRedirect(self.get_success_url()) 
        else:
            messages.info(self.request, "Tidak ada perubahan yang disimpan.")
            return HttpResponseRedirect(self.get_success_url())

    def test_func(self):
        article = self.get_object()
        return self.request.user == article.author or self.request.user.is_superuser


# --- DELETE View ---

class ArticleDeleteView(SuccessMessageMixin, LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Article
    template_name = 'news/article_confirm_delete.html'
    success_url = reverse_lazy('news:article-list')

    def post(self, request, *args, **kwargs):

        self.object = self.get_object()
        title_to_delete = self.object.title 

        response = super().post(request, *args, **kwargs) 
        
        messages.error(self.request, f"Artikel '{title_to_delete}' berhasil dihapus!") 
        
        return response

    def test_func(self):
        article = self.get_object()
        return self.request.user == article.author or self.request.user.is_superuser