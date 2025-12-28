from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
	list_display = (
		"registration_number",
		"department",
		"course",
		"interest_type",
		"experience_level",
	)
	search_fields = ("registration_number", "name", "department", "course")
