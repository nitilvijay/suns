from rest_framework import serializers
from .models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            "id",
            "name",
            "registration_number",
            "department",
            "course",
            "year",
            "interest_type",
            "preferred_roles",
            "experience_level",
            "campus_oss_repos",
            "external_oss_contributions",
            "profile_json",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
