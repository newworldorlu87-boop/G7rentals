from django.urls import path
from . import views
from .views import profile_view

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/tenant/', views.tenant_dashboard, name='tenant_dashboard'),
    path('dashboard/landlord/', views.landlord_dashboard, name='landlord_dashboard'),
    path('profile/', views.profile_view, name='profile'),
    
    path('verify/<uuid:token>/', views.verify_email, name='verify_email'),

    path('reset/', views.request_password_reset, name='reset_request'),
    path('reset-password/<uuid:token>/', views.reset_password, name='reset_password'),
    
    
    

]
