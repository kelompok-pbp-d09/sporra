from django.db import models
from django.contrib.auth.models import User
from event.models import Event
from decimal import Decimal

class Ticket(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="tickets")
    ticket_type = models.CharField(max_length=50, choices=[
        ('regular', 'Regular'),
        ('vip', 'VIP'),
    ])
    price = models.DecimalField(max_digits=15, decimal_places=2)
    available = models.PositiveIntegerField(default=0)  # sisa tiket tersedia
    class Meta:
        unique_together = ('event', 'ticket_type')  # <--- mencegah tipe yang sama di 1 event
    def __str__(self):
        return f"{self.ticket_type} - {self.event.judul}"

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    booked_at = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(
        max_digits=15, decimal_places=2,
        default=Decimal('0.00')  )

    def __str__(self):
        return f"{self.user.username} - {self.ticket.event.judul}"

    class Meta:
        unique_together = ('user', 'ticket')  # biar user gak pesan tiket yg sama dua kali
