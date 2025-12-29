from rest_framework import serializers
from .models import Resume


class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = ["id", "profile", "file", "raw_text", "parsed_json", "uploaded_at"]
        read_only_fields = ["id", "raw_text", "parsed_json", "uploaded_at"]
