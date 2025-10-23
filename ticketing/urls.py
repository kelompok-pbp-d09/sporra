from django.urls import path
from . import views

app_name = 'ticketing'

urlpatterns = [
    path('event/<int:event_id>/tickets/', views.list_tickets, name='list_tickets'),
    path('book/<int:ticket_id>/', views.book_ticket, name='book_ticket'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('tickets/', views.all_tickets, name='all_tickets'),


]
