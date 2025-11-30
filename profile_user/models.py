from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import F
from django.db.models.functions import Greatest

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
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    events_created = models.IntegerField(default=0)


    def __str__(self):
        return f"{self.user.username} ({self.role})"

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def komentar_created(self):
        """Menghitung jumlah Post (komentar) user secara real-time."""
        from forumdiskusi.models import Post
        return Post.objects.filter(author=self.user).count()

    @property
    def news_created(self):
        """Menghitung jumlah Article (news) user secara real-time."""
        from news.models import Article
        return Article.objects.filter(author=self.user).count()

    def add_status(self, content):
        return Status.objects.create(user=self, content=content)

    def get_statuses(self):
        return self.statuses.all()

class Status(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='statuses')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)



