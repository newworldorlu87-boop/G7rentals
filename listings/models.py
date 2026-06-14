from django.db import models
from accounts.models import User


class Property(models.Model):
    PROPERTY_TYPE_CHOICES = [
        ('apartment', 'Apartment'),
        ('house', 'House'),
        ('studio', 'Studio'),
        ('condo', 'Condo'),
        ('townhouse', 'Townhouse'),
        ('commercial', 'Commercial'),
    ]

    STATUS_CHOICES = [
        ('vacant', 'Vacant'),
        ('occupied', 'Occupied'),
        ('maintenance', 'Under Maintenance'),
    ]

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='properties'
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # Price
    price = models.DecimalField(max_digits=12, decimal_places=2)

    # Location fields
    address = models.CharField(max_length=255, default="")
    city = models.CharField(max_length=100, default="Abuja")
    state = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=255, blank=True, help_text="Neighborhood or area description")

    # Property details
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES, default='apartment')
    bedrooms = models.PositiveIntegerField(default=1)
    bathrooms = models.DecimalField(max_digits=3, decimal_places=1, default=1.0)
    sqft = models.PositiveIntegerField(default=0, verbose_name="Square Feet")

    # Media
    image = models.ImageField(upload_to='properties/')

    # Status & availability
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='vacant')
    is_available = models.BooleanField(default=True)

    # Amenities
    amenities = models.CharField(max_length=500, blank=True, help_text="Comma-separated: Pool, Gym, WiFi, etc.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.city}"

    @property
    def display_price(self):
        return f"₦{self.price:,.2f}"

    @property
    def tenant(self):
        """Return current tenant if property is occupied."""
        from bookings.models import Booking
        booking = Booking.objects.filter(
            property=self,
            status='approved'
        ).select_related('tenant').first()

        return booking.tenant if booking else None

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
        unique_together = ('user', 'property')

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

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender} → {self.receiver}"
    