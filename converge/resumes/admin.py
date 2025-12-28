from django.contrib import admin

from .models import Resume


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
	list_display = ("profile", "uploaded_at")
	search_fields = ("profile__registration_number",)
