from django.db import models

from profiles.models import Profile

#Here we have to return the output of Gemini!!!!!!!!!!!!!!!!!!!!!
#!!!!!!!!!!!!!!!!!!!!!!!
class Resume(models.Model):
	profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name="resume")
	file = models.FileField(upload_to="resumes/")
	raw_text = models.TextField(blank=True)
	parsed_json = models.JSONField(default=dict, blank=True)
	uploaded_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"Resume for {self.profile.registration_number}"
