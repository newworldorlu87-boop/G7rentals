from django.contrib import admin
from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('rentals.urls')),
    path('', include('accounts.urls')),
    path('', include('bookings.urls')),
    path('', include('payments.urls')),
    path('', include('properties.urls')),
    path('', include('reviews.urls')),
    path('', include('listings.urls')),
    path('dashboard/', include('dashboard.urls')),
]
 

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)