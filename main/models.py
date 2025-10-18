from django.db import models

# Create your models here.
class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateTimeField()
    locaton = models.CharField(max_length=300)

    def __str__(self):
        return self.title
    
class Participant(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    event = models.ForeignKey(Event, related_name='participants', on_delete=models.CASCADE)

    def __str__(self):
        return self.name