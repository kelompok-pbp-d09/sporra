from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('user', 'User'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    bio = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    # profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    # sport_interest = models.CharField(max_length=100, blank=True, null=True)
    # joined_date = models.DateTimeField(auto_now_add=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')  # 👈 Role field ditambahkan

    post_created = models.PositiveIntegerField(default=0) #banyak post yang telah dibuat
    news_created = models.PositiveIntegerField(default=0) #banyak berita yang telah dibuat


    def __str__(self):
        return f"{self.user.username} ({self.role})"

    @property
    def is_admin(self):
        return self.role == 'admin'
    
    def increment_post(self):
        self.post_created += 1
        self.save()

    def increment_news(self):
        self.news_created += 1
        self.save()

    #tambahkan fitur event yang sedang diikuti
    #edit profile picture, bio,username,no telepon dengan (sudah sekalian form)
    #filter informasi
    #

