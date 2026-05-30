from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', include('listings.urls')),
    path('', include('accounts.urls')),
    path('', include('bookings.urls')),
    path('', include('payments.urls')),
    path('', include('properties.urls')),
    path('', include('reviews.urls')),

    path('dashboard/', include('dashboard.urls')),

    # Django Allauth
    path('accounts/', include('allauth.urls')),
]

urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)