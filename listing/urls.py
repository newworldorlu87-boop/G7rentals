from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),      # Changed: added accounts/ prefix
    path('', include('listings.urls')),               # Home, properties, static pages
    path('bookings/', include('bookings.urls')),
    path('payments/', include('payments.urls')),
    path('properties/', include('properties.urls')),    # If this is different from listings
    path('reviews/', include('reviews.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('social/', include('allauth.urls')),         # Changed: avoid conflict with accounts
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)