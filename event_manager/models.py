from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.
class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateTimeField()
    location = models.CharField(max_length=200)
    total_seats = models.PositiveIntegerField()
    remaining_seats = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(User, related_name='liked_events', blank=True)
    
    def __str__(self):
        return self.title
    
    def get_likes_count(self):
        return self.likes.count()
    
    def get_comments_count(self):
        return self.comments.count()
    
    def calculate_remaining_seats(self):
        registrations_count = self.registrations.aggregate(models.Sum('num_seats'))['num_seats__sum'] or 0
        self.remaining_seats = self.total_seats - registrations_count
        self.save()
        return self.remaining_seats

class Comment(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.event.title}"

class EventRegistration(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='registrations')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    num_seats = models.PositiveIntegerField(default=1)
    registration_date = models.DateTimeField(default=timezone.now)
    payment_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], default='pending')
    
    def __str__(self):
        return f"{self.name} - {self.event.title}"
    
    def save(self, *args, **kwargs):
        if not self.pk:  # If this is a new registration
            # Make sure there are enough seats
            if self.event.remaining_seats >= self.num_seats:
                super().save(*args, **kwargs)
                self.event.calculate_remaining_seats()
            else:
                raise ValueError("Not enough seats available")
        else:
            super().save(*args, **kwargs)
