from django.urls import path
from . import views

app_name = 'forumdiskusi'

urlpatterns = [
    path('<uuid:pk>/', views.forum, name='forum'),
    path('<uuid:pk>/add_comment/', views.add_comment, name='add_comment'),
    path('delete_comment/<int:post_id>/', views.delete_comment, name='delete_comment'),
]
