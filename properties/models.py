from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class Property(models.Model):
    PROPERTY_TYPE = (
        ('house', 'House'),
        ('apartment', 'Apartment'),
        ('land', 'Land'),
    )

    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()

    price = models.DecimalField(max_digits=12, decimal_places=2)
    location = models.CharField(max_length=255)
    city = models.CharField(max_length=100)

    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE)

    bedrooms = models.IntegerField(default=0)
    bathrooms = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='properties/')
    
class Inquiry(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)