from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import CustomUser


# Register your models here.
class CustomUserAdmin(UserAdmin):
    """
    Helps to access Django's built-in web interface for database.
    :param list_display: the details to be shown in overview (without opening individual record)
    :param fieldsets: groups of fields (how to show them, how to group them under a heading)
    """
    model = CustomUser
    list_display = ("username", "email", "role", "is_staff", "is_active")
    fieldsets = UserAdmin.fieldsets + (
        (None, {"fields" : ("role", "phone_number")}),
    )

admin.site.register(CustomUser, CustomUserAdmin)