from django.contrib import admin
from core.models import ContactMessage

class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "email", "subject", "created_at", "is_read")
    list_filter = ("is_read",)
    search_fields = ("first_name", "last_name", "email", "message")
    readonly_fields = ("first_name", "last_name", "email", "phone", "subject", "message", "created_at")

    def has_add_permission(self, request):
        return False