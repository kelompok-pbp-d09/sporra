# news/urls.py

from django.urls import path
from . import views

app_name = 'news'

urlpatterns = [
    path('', views.ArticleListView.as_view(), name='article-list'),
    
    # SEBELUMNYA: path('articles/new/', ...)
    path('new/', views.ArticleCreateView.as_view(), name='article-create'),
    
    # SEBELUMNYA: path('articles/<uuid:pk>/', ...)
    path('<uuid:pk>/', views.ArticleDetailView.as_view(), name='article-detail'),
    
    # SEBELUMNYA: path('articles/<uuid:pk>/edit/', ...)
    path('<uuid:pk>/edit/', views.ArticleUpdateView.as_view(), name='article-update'),
    
    # SEBELUMNYA: path('articles/<uuid:pk>/delete/', ...)
    path('<uuid:pk>/delete/', views.ArticleDeleteView.as_view(), name='article-delete'),
]