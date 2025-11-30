from event.views import home_event, event_detail, create_event, edit_event, delete_event, get_events_ajax, get_event_ajax, create_event_flutter
from django.urls import path

app_name = 'event'

urlpatterns = [
    path('', home_event, name='home_event'),
    path('event/<uuid:id>/', event_detail, name='event_detail'),
    path('create-event/', create_event, name='create_event'),
    path('event/<str:id>/edit/', edit_event, name='edit_event'),
    path('event/<str:id>/delete/', delete_event, name='delete_event'),
    path('ajax/get-event/<uuid:id>/', get_event_ajax, name='get_event_ajax'),
    path('ajax/get-events/', get_events_ajax, name='get_events_ajax'),
    path('json/', get_events_ajax, name='event_json'),
]