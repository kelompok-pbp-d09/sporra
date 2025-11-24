from django.urls import path
from profile_user.views import *
from . import views


app_name = 'profile_user'

urlpatterns = [
    path('',show_profile,name='show_profile'),
    path('register/', register_user, name='register'),
    path('login/', login_user, name='login'),
    path('logout/', logout_user, name='logout'),
    path('edit/', edit_profile, name='edit_profile'),
    path('add_status/', add_status, name='add_status'),
    path('delete_status/<int:status_id>/', delete_status, name='delete_status'),
    path('edit_status/<int:status_id>/', edit_status, name='edit_status'),  
    path('<str:username>/', views.show_profile, name='show_profile'),
    path('register/', register_flutter, name='register_flutter'),
    path('logout/', logout_flutter, name='logout_flutter'),
]