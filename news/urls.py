from django.urls import path
from . import views

app_name = 'news'

urlpatterns = [
    path('', views.ArticleListView.as_view(), name='article-list'),
    
    path('new/', views.ArticleCreateView.as_view(), name='article-create'),
    
    path('<uuid:pk>/', views.ArticleDetailView.as_view(), name='article-detail'),
    
    path('<uuid:pk>/edit/', views.ArticleUpdateView.as_view(), name='article-update'),
    
    path('<uuid:pk>/delete/', views.ArticleDeleteView.as_view(), name='article-delete'),
    
    path('proxy-image/', views.proxy_image, name='proxy_image'),
    
    path('json/', views.show_json, name='show_json'), 
    path('json/<str:id>/', views.show_json_by_id, name='show_json_by_id'),
    path('delete-flutter/<str:id>/', views.delete_article_flutter, name='delete_article_flutter'),
    path('edit-flutter/<str:id>/', views.edit_article_flutter, name='edit_article_flutter'),
]