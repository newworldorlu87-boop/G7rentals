from django.db import models
from properties.models import Property
from django.conf import settings

User = settings.AUTH_USER_MODEL

class Review(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comment = models.TextField()