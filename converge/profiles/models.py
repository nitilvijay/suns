from django.db import models


class Profile(models.Model):
	INTEREST_CHOICES = [
		("research", "Research"),
		("project", "Project"),
		("both", "Both"),
	]

	name = models.CharField(max_length=255, blank=True)
	registration_number = models.CharField(max_length=64, unique=True)
	department = models.CharField(max_length=128, blank=True)
	course = models.CharField(max_length=128, blank=True)
	year = models.PositiveIntegerField(null=True, blank=True)
	interest_type = models.CharField(max_length=16, choices=INTEREST_CHOICES, default="both")
	preferred_roles = models.CharField(max_length=255, blank=True)
	experience_level = models.CharField(max_length=64, blank=True)
	profile_json = models.JSONField(default=dict, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.registration_number
