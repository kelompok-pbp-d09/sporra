from django.db import models
from django.contrib.auth.models import User

class ForumDiskusi(models.Model):
    # Relasi ke Article, gunakan UUID sebagai foreign key
    article = models.ForeignKey('news.Article', on_delete=models.CASCADE, related_name='forum_diskusi')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Forum Diskusi untuk: {self.article.title}"


class Post(models.Model):
    forum = models.ForeignKey(ForumDiskusi, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author.username}: {self.content[:30]}"


# UserProfile untuk role admin kustom
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username
