from django.urls import path
from . import views

app_name = 'forumdiskusi'

urlpatterns = [
    path('preview/', views.preview, name='preview'),
    path('<uuid:pk>/', views.forum, name='forum'),
    path('<uuid:pk>/add_comment/', views.add_comment, name='add_comment'),
    path('delete_comment/<int:post_id>/', views.delete_comment, name='delete_comment'),
    path('post/<int:post_id>/vote/', views.vote_post, name='vote_post'), 
]
