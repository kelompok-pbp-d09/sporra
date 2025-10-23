from django.db import models
from django.contrib.auth.models import User

class ForumDiskusi(models.Model):
    article = models.ForeignKey('news.Article', on_delete=models.CASCADE, related_name='forum_diskusi', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Forum Diskusi untuk: {self.article.title}"


class Post(models.Model):
    forum = models.ForeignKey(ForumDiskusi, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    score = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.author.username}: {self.content[:30]}"
    
class Vote(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    value = models.SmallIntegerField(default=0)  # +1 = upvote, -1 = downvote

    class Meta:
        unique_together = ('post', 'user')  

    def __str__(self):
        return f"{self.user.username} voted {self.value} on {self.post.id}"

