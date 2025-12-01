from django.urls import path
from ticketing import views 

app_name = 'ticketing'

urlpatterns = [
    # === HALAMAN WEB (HTML) ===
    path('tickets/', views.all_tickets, name='all_tickets'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),

    # === API & AJAX ENDPOINTS (JSON) ===
    
    # 1. Booking Tiket 
    # Pastikan Event ID di models.py kamu pakai UUID. Jika pakai Integer, ganti <uuid:event_id> jadi <int:event_id>
    path('book/<uuid:event_id>/', views.book_ticket, name='book_ticket'),
    
    # 2. Get Data Tiket
    path('tickets/data/', views.get_tickets_ajax, name='get_tickets'),
    
    # 3. Get Booking User
    path('api/my-bookings/', views.get_my_bookings_ajax, name='get_my_bookings_ajax'),
    
    # 4. Create Ticket (FIXED: Ubah 'create/' menjadi 'create-ticket/')
    path('create-ticket/', views.create_ticket, name='create_ticket'),

    # 5. Edit & Delete (Pastikan Ticket ID adalah Integer/AutoField)
    path('edit_ticket_ajax/<int:ticket_id>/', views.edit_ticket_ajax, name='edit_ticket_ajax'),
    path('delete_ticket_ajax/<int:ticket_id>/', views.delete_ticket_ajax, name='delete_ticket_ajax'),
    
    # 6. Dropdown Event User
    path('get-user-events/', views.get_user_events_dropdown, name='get_user_events_dropdown'),
]