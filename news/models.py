# models.py
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.db.models import F
from django.urls import reverse

class Article(models.Model):
    
    CATEGORY_CHOICES = [
        ('sepakbola', 'Sepakbola'),
        ('f1', 'F1'),
        ('moto gp', 'Moto GP'),
        ('raket', 'Raket'),
        ('olahraga lain', 'Olahraga Lain')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    content = models.TextField()
    thumbnail = models.URLField(blank=True, null=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='sepakbola')
    
    # --- THIS IS THE KEY CHANGE ---
    # We make the author nullable.
    # on_delete=models.SET_NULL means if the author User is deleted,
    # this field becomes Null (the article isn't deleted).
    
    author = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,  # Allows the field to be NULL in the database
        blank=True, # Allows the field to be blank in forms
        related_name='articles'
    )
    
    news_views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
        
    def get_absolute_url(self):
        return reverse('news:article-detail', kwargs={'pk': self.pk})

    @property
    def is_news_hot(self):
        return self.news_views > 20
        
    def increment_views(self):
        self.news_views = F('news_views') + 1
        self.save(update_fields=['news_views'])
        self.refresh_from_db()