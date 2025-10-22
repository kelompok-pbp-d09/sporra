from django.urls import path
from . import views

app_name = 'forumdiskusi'

urlpatterns = [
    path('<slug:slug>/', views.forum, name='forum'),
    path('<slug:slug>/add_comment/', views.add_comment, name='add_comment'),
    path('delete_comment/<int:post_id>/', views.delete_comment, name='delete_comment'),
]
