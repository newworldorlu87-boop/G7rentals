from django.db import models
from accounts.models import User
  

class Property(models.Model):
    PROPERTY_TYPE = [
        ('apartment', 'Apartment'),
        ('house', 'House'),
        ('studio', 'Studio'),
    ]

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='listings_properties'
    )

    title = models.CharField(max_length=200)
    description = models.TextField()

    price = models.DecimalField(max_digits=10, decimal_places=2)

    # 🔥 Location fields (aligned with your dashboard)
    city = models.CharField(max_length=100, default="Abuja")
    location = models.CharField(max_length=255)

    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE)

    image = models.ImageField(upload_to='properties/')

    created_at = models.DateTimeField(auto_now_add=True)


    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} - {self.city}"
class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites'
    )

    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='favorited_by'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'property')  # prevent duplicates

    def __str__(self):
        return f"{self.user.username} ❤️ {self.property.title}"   

class Message(models.Model):

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )

    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_messages'
    )

    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE
    )

    name = models.CharField(max_length=100)

    email = models.EmailField()

    message = models.TextField()

    # NEW
    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender} → {self.receiver}"