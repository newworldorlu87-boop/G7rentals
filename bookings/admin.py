from django.contrib import admin
from .models import Booking

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'property', 'tenant', 'landlord', 'status', 'start_date', 'end_date', 'total_price', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['tenant__username', 'property__title']
    list_editable = ['status']