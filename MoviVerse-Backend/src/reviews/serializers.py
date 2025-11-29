from rest_framework import serializers
from .models import Review

class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = Review
        fields = ("id", "user", "movie", "rating", "text", "created_at")
        read_only_fields = ("user", "created_at")
