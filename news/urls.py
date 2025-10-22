from django.urls import path
from . import views

app_name = 'news'

urlpatterns = [
    # URL for the list of articles. E.g., [yoursite.com/news/](https://yoursite.com/news/)
    path('', views.article_list, name='article_list'),
    
    # URL for a single article. E.g., [yoursite.com/news/real-madrid-wins-again/](https://yoursite.com/news/real-madrid-wins-again/)
    path('<slug:slug>/', views.article_detail, name='article_detail'),
]