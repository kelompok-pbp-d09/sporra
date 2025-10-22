from main.views import home_event, event_detail, create_event, edit_event
from django.urls import path

app_name = 'main'

urlpatterns = [
    path('', home_event, name='home_event'),
    path('event/<uuid:id>/', event_detail, name='event_detail'),
    path('create-event/', create_event, name='create_event'),
    path('event/<uuid:id>/edit/', edit_event, name='edit_event'),
]