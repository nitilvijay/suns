from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
	list_display = ("title", "project_type", "owner_profile", "created_at")
	list_filter = ("project_type",)
	search_fields = (
		"title",
		"description",
		"github_url",
		"owner_profile__registration_number",
	)
