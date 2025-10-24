from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('user', 'User'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    bio = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.URLField(blank=True, null=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')  #Role field 
    komentar_created = models.PositiveIntegerField(default=0) #banyak komentar yang telah dipost
    news_created = models.PositiveIntegerField(default=0) #banyak berita yang telah dibuat
    # events_created = models.PositiveIntegerField(default=0) #banyak event yang telah dibuat


    def __str__(self):
        return f"{self.user.username} ({self.role})"

    @property
    def is_admin(self):
        return self.role == 'admin'
    
    def increment_komentar(self):
        self.komentar_created += 1
        self.save()

    def increment_news(self):
        self.news_created += 1
        self.save()

    # def increment_events(self):
    #     self.events_created += 1
    #     self.save()

    def add_status(self, content):
        return Status.objects.create(user=self, content=content)

    def get_statuses(self):
        return self.statuses.all()

    #filter informasi
    #STATUS

class Status(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='statuses')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)



