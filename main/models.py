from django.db import models
from django.contrib.auth.models import User
import uuid

# Create your models here.
class Event(models.Model):
    CATEGORY_CHOICES = [
        ('basket', 'Basket'),
        ('tennis', 'Tennis'),
        ('padel', 'Padel'),
        ('badminton', 'Badminton'),
        ('cricket', 'Cricket'),
        ('volleyball', 'Volleyball'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateTimeField()
    price = models.IntegerField(default=0)
    location = models.CharField(max_length=300)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_views = models.PositiveIntegerField(default=0)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='basket')
    Max_participants = models.PositiveIntegerField(default=0)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.title
    
    def increment_views(self):
        self.event_views += 1
        self.save()
        