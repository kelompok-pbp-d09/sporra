from django.urls import path
from ticketing import views  # Pastikan import ini benar

app_name = 'ticketing'

urlpatterns = [
    # === HALAMAN WEB (HTML) ===
    path('tickets/', views.all_tickets, name='all_tickets'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),

    # === API & AJAX ENDPOINTS (JSON) ===
    # Digunakan oleh Flutter dan JavaScript di Web
    
    # 1. Booking Tiket (POST)
    path('book/<uuid:event_id>/', views.book_ticket, name='book_ticket'),
    
    # 2. Get Data Tiket (GET)
    path('tickets/data/', views.get_tickets_ajax, name='get_tickets'),
    
    # 3. Get Booking User (GET)
    path('api/my-bookings/', views.get_my_bookings_ajax, name='get_my_bookings_ajax'),
    
    # 4. Create Ticket (POST)
    path('create/', views.create_ticket, name='create_ticket'),

path('edit_ticket_ajax/<int:ticket_id>/', views.edit_ticket_ajax, name='edit_ticket_ajax'),
path('delete_ticket_ajax/<int:ticket_id>/', views.delete_ticket_ajax, name='delete_ticket_ajax'),

]