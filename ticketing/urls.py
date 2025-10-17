from django.urls import path
from . import views

app_name = 'ticketing'

urlpatterns = [
    path('', views.index, name='index'),
]
