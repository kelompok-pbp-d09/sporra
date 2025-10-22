from django.db import models
from django.contrib.auth.models import User

# Model ini menghubungkan forum ke satu news tertentu
class ForumDiskusi(models.Model):
    news = models.ForeignKey('news.News', on_delete=models.CASCADE, related_name='forum_diskusi')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Forum Diskusi untuk: {self.news.title}"


# Setiap postingan yang muncul di forum diskusi
class Post(models.Model):
    forum = models.ForeignKey(ForumDiskusi, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author.username}: {self.content[:30]}"

# Sementara karena belum ada modul User
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

