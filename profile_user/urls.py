from django.urls import path
from profile_user.views import *

app_name = 'profile_user'

urlpatterns = [
    path('',show_profile,name='show_profile'),  
    path('<str:username>/', show_profile, name='show_profile'),
    path('<int:id>/', show_profile, name='show_profile'),
    path('register/', register_user, name='register'),
    path('login/', login_user, name='login'),
    path('logout/', logout_user, name='logout'),
    path('register/', register_user, name='register'),
    path('edit/', edit_profile, name='edit_profile'),
    path('add_status/', add_status, name='add_status'),
    path('delete_status/<int:status_id>/', delete_status, name='delete_status'),
    path('edit_status/<int:status_id>/', edit_status, name='edit_status'),
    path('auth/login/', login_flutter, name='login_flutter'),
    path('auth/register/', register_flutter, name='register_flutter'),
    path('api/logout/', logout_flutter, name='logout_flutter'),
    path('user/<str:username>/', show_profile, name='user_profile'),
]