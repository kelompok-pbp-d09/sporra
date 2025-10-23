from django.db import models
from django.contrib.auth.models import User
import uuid

# Create your models here.
class Event(models.Model):
    CATEGORY_CHOICES = [
        ('basket', 'Basket'),
        ('tennis', 'Tennis'),
        ('bulu tangkis', 'Bulu Tangkis'),
        ('volley', 'Volley'),
        ('futsal', 'Futsal'),
        ('sepak bola', 'Sepak Bola'),
        ('renang', 'Renang'),
        ('lainnya', 'Lainnya'),
    ]

    judul = models.CharField(max_length=255)
    deskripsi = models.TextField()
    date = models.DateTimeField()
    harga = models.IntegerField(default=0)
    lokasi = models.CharField(max_length=300)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_views = models.PositiveIntegerField(default=0)
    kategori = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='basket')
    maksimal_peserta = models.PositiveIntegerField(default=0)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.judul

    def increment_views(self):
        self.event_views += 1
        self.save()