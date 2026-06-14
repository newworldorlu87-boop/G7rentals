# bookings/models.py
from django.db import models
from django.conf import settings


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    property = models.ForeignKey(
        'listings.Property',
        on_delete=models.CASCADE,
        related_name='bookings'
    )

    tenant = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
    related_name='tenant_bookings',
    null=True,
    blank=True
    )

    # Optional: store landlord reference for quick lookup
    landlord = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='landlord_bookings',
        null=True,
        blank=True
    )

    start_date = models.DateField()
    end_date = models.DateField()
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.tenant.username} → {self.property.title} ({self.status})"

    def save(self, *args, **kwargs):
        # Auto-set landlord from property owner
        if not self.landlord_id and self.property_id:
            self.landlord = self.property.owner
        super().save(*args, **kwargs)