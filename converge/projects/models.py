from django.db import models

from profiles.models import Profile


class Project(models.Model):
	TYPE_CHOICES = [
		("campus_closed", "Campus Closed"),
		("campus_oss", "Campus Open Source"),
		("external_oss", "External Open Source"),
	]

	title = models.CharField(max_length=255)
	description = models.TextField()
	project_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
	github_url = models.URLField(blank=True)
	owner_profile = models.ForeignKey(
		Profile, null=True, blank=True, on_delete=models.SET_NULL, related_name="projects"
	)
	metadata = models.JSONField(default=dict, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.title
