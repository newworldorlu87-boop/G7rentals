from django.db import models
from listings.models import Property
from django.conf import settings

User = settings.AUTH_USER_MODEL

class Booking(models.Model):

    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE
    )

    start_date = models.DateField()

    end_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    def __str__(self):
        return f"{self.user.email} booked {self.property.title}"
    