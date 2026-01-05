from django.db import models


class Rating(models.Model):
	"""Peer rating submitted after project completion."""
	rater_id = models.IntegerField(db_index=True)
	ratee_id = models.IntegerField(db_index=True)
	project_id = models.CharField(max_length=64, db_index=True)
	category_scores = models.JSONField(default=dict)
	raw_rating = models.FloatField()
	adjusted_rating = models.FloatField()
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		db_table = "ratings"
		indexes = [
			models.Index(fields=["ratee_id"]),
			models.Index(fields=["rater_id"]),
			models.Index(fields=["project_id"]),
		]

	def __str__(self):
		return f"Rating {self.rater_id} -> {self.ratee_id} ({self.project_id})"
