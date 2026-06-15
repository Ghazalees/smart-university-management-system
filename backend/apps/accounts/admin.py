from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Department, Permission, Profile, Role, User, UserRole

admin.site.register(User, UserAdmin)
admin.site.register([Department, Permission, Profile, Role, UserRole])
