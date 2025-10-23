from django.urls import path
from . import views

app_name = 'ticketing'

urlpatterns = [
    path('book/<uuid:event_id>/', views.book_ticket, name='book_ticket'),  
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('tickets/data/', views.get_tickets, name='get_tickets'),    # endpoint ajax
    path('tickets/', views.all_tickets, name='all_tickets'),
    path('create/', views.create_ticket, name='create_ticket'),
]
