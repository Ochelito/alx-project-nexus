from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Movie, Genre, Review, Favorite, Recommendation, Watchlist,
    MovieViewLog, TrendingMovie
)

User = get_user_model()

# ---------- User serializers ----------
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "username")


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "email", "username", "password")

    def create(self, validated_data):
        user = User(
            email=validated_data["email"],
            username=validated_data["username"]
        )
        user.set_password(validated_data["password"])
        user.save()
        return user


# ---------- Genre ----------
class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ("id", "name")


# ---------- Movie & related ----------
class MovieSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    class Meta:
        model = Movie
        fields = (
            "id", "tmdb_id", "title", "description", "release_year",
            "genres", "created_at", "updated_at"
        )
        read_only_fields = ("created_at", "updated_at")


# For admin to create/edit movie including genre ids
class MovieCreateUpdateSerializer(serializers.ModelSerializer):
    genre_ids = serializers.ListField(write_only=True, required=False, child=serializers.IntegerField())

    class Meta:
        model = Movie
        fields = ("id", "tmdb_id", "title", "description", "release_year", "genre_ids")

    def create(self, validated_data):
        genre_ids = validated_data.pop("genre_ids", [])
        movie = super().create(validated_data)
        if genre_ids:
            movie.genres.set(genre_ids)
        return movie

    def update(self, instance, validated_data):
        genre_ids = validated_data.pop("genre_ids", None)
        instance = super().update(instance, validated_data)
        if genre_ids is not None:
            instance.genres.set(genre_ids)
        return instance


# ---------- Review ----------
class ReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Review
        fields = ("id", "user", "movie", "rating", "review_text", "created_at", "updated_at")
        read_only_fields = ("user", "created_at", "updated_at")


# ---------- Favorite ----------
class FavoriteSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Favorite
        fields = ("id", "user", "movie", "created_at")
        read_only_fields = ("user", "created_at")


# ---------- Watchlist ----------
class WatchlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Watchlist
        fields = ("id", "user", "movie", "created_at")
        read_only_fields = ("user", "created_at")


# ---------- Recommendation ----------
class RecommendationSerializer(serializers.ModelSerializer):
    movie = MovieSerializer(read_only=True)
    class Meta:
        model = Recommendation
        fields = ("id", "movie", "reason", "created_at")
        read_only_fields = ("created_at",)


# ---------- Movie view log ----------
class MovieViewLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieViewLog
        fields = ("id", "user", "movie", "timestamp")
        read_only_fields = ("timestamp",)


# ---------- Trending ----------
class TrendingMovieSerializer(serializers.ModelSerializer):
    movie = MovieSerializer(read_only=True)
    class Meta:
        model = TrendingMovie
        fields = ("id", "movie", "score", "period", "updated_at")
