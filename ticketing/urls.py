from django.urls import path
from . import views

app_name = 'ticketing'

urlpatterns = [
    path('book/<uuid:event_id>/', views.book_ticket, name='book_ticket'),  
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('tickets/data/', views.get_tickets_ajax, name='get_tickets'),    # endpoint ajax
    path('tickets/', views.all_tickets, name='all_tickets'),
    path('create/', views.create_ticket, name='create_ticket'),
    path('ajax/my_bookings/', views.get_my_bookings_ajax, name='get_my_bookings_ajax'),  # JSON untuk AJAX
    path('edit_ticket_ajax/<int:ticket_id>/', views.edit_ticket_ajax, name='edit_ticket_ajax'),  # Edit via AJAX
    path('delete_ticket_ajax/<int:ticket_id>/', views.delete_ticket_ajax, name='delete_ticket_ajax'),  # Delete via AJAX

]
