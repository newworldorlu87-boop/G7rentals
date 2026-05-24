from django.contrib import admin
from.models import User,Profile


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('user_type','phone', 'email')
    list_filter = ()


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user','city','address','country','bio','company_name','business_address','created_at')
