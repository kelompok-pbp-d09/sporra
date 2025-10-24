from django.urls import path
from . import views

app_name = 'news'

urlpatterns = [
    path('', views.ArticleListView.as_view(), name='article-list'),
    
    path('new/', views.ArticleCreateView.as_view(), name='article-create'),
    
    path('<uuid:pk>/', views.ArticleDetailView.as_view(), name='article-detail'),
    
    path('<uuid:pk>/edit/', views.ArticleUpdateView.as_view(), name='article-update'),
    
    path('<uuid:pk>/delete/', views.ArticleDeleteView.as_view(), name='article-delete'),
]