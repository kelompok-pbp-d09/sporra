from django.urls import path
from profile_user.views import *


app_name = 'profile_user'

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login_user, name='login'),
    path('logout/', logout_user, name='logout'),

]