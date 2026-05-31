from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('listings.urls')),
    path('', include('accounts.urls')),
    path('', include('bookings.urls')),
    path('', include('payments.urls')),
    path('', include('properties.urls')),
    path('', include('reviews.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('accounts/', include('allauth.urls')),
]

# Serve media files in development
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# 🔥 FALLBACK: Explicitly serve media in production (Render)
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
]