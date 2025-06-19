from django.contrib import admin
from .models import Lead, Inquiry

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'created_at')

@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ('lead', 'message', 'submitted_at')