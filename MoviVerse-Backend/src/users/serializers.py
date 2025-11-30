from rest_framework import serializers
from .models import User, Recommendation
from django.contrib.auth.password_validation import validate_password
from movies.serializers import MovieSerializer
from movies.models import Movie

# -----------------------------
# User Serializers
# -----------------------------
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    preferred_genres = serializers.ListField(
        child=serializers.IntegerField(), required=False, default=list
    )

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'preferred_genres']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    preferred_genres = serializers.ListField(
        child=serializers.IntegerField(), required=False, default=list
    )

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "preferred_genres"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


# -----------------------------
# Recommendation Serializer
# -----------------------------
class RecommendationSerializer(serializers.ModelSerializer):
    movie = serializers.SerializerMethodField()

    class Meta:
        model = Recommendation
        fields = ["id", "movie_id", "movie", "reason", "created_at"]

    def get_movie(self, obj):
        try:
            movie = Movie.objects.get(tmdb_id=obj.movie_id)
            return MovieSerializer(movie).data
        except Movie.DoesNotExist:
            return None
