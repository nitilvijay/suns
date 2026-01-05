from rest_framework import serializers
from .models import Rating


class RatingSerializer(serializers.ModelSerializer):
	class Meta:
		model = Rating
		fields = [
			"id",
			"rater_id",
			"ratee_id",
			"project_id",
			"category_scores",
			"raw_rating",
			"adjusted_rating",
			"created_at",
		]
		read_only_fields = ["id", "raw_rating", "adjusted_rating", "created_at"]


class SubmitRatingSerializer(serializers.Serializer):
	rater_id = serializers.IntegerField()
	ratee_id = serializers.IntegerField()
	project_id = serializers.CharField(max_length=64)
	category_scores = serializers.JSONField()
	
	def to_internal_value(self, data):
		"""Convert string IDs to integers if needed."""
		data = data.copy() if hasattr(data, 'copy') else dict(data)
		if 'rater_id' in data and isinstance(data['rater_id'], str):
			data['rater_id'] = int(data['rater_id'])
		if 'ratee_id' in data and isinstance(data['ratee_id'], str):
			data['ratee_id'] = int(data['ratee_id'])
		return super().to_internal_value(data)
