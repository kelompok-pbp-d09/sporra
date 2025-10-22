from django.urls import path
from . import views

app_name = 'forumdiskusi'

urlpatterns = [
    path('<int:news_id>/', views.forum, name='forum'),
    path('<int:news_id>/add_comment/', views.add_comment, name='add_comment'),
    path('delete_comment/<int:post_id>/', views.delete_comment, name='delete_comment'),
]
