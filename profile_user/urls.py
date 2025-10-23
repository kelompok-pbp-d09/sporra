from django.urls import path
from profile_user.views import *


app_name = 'profile_user'

urlpatterns = [
    path('',show_profile,name='show_profile'),
    path('register/', register_user, name='register'),
    path('login/', login_user, name='login'),
    path('logout/', logout_user, name='logout'),
    path('edit/', edit_profile, name='edit_profile'),
]