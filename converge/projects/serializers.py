from rest_framework import serializers
from .models import Project


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            "id",
            "title",
            "description",
            "project_type",
            "github_url",
            "owner_profile",
            "metadata",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
