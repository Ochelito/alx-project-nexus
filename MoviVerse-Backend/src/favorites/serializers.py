from rest_framework import serializers
from .models import Favorite
from movies.serializers import MovieSerializer
from movies.models import Movie

class MovieBasicSerializer(serializers.ModelSerializer):
    """
    Simple serializer for movie details nested in favorites.
    """
    class Meta:
        model = Movie
        fields = ["tmdb_id", "title", "poster_path", "vote_average"]

class FavoriteSerializer(serializers.ModelSerializer):
    movie = MovieSerializer(read_only=True)
    movie_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Favorite
        fields = ["id", "user", "movie", "movie_id", "created_at"]
        read_only_fields = ["id", "user", "movie", "created_at"]

    def create(self, validated_data):
        user = self.context["request"].user
        tmdb_id = validated_data.pop("movie_id")

        # Get or create the movie object
        movie, _ = Movie.objects.get_or_create(
            tmdb_id=tmdb_id,
            defaults={"title": validated_data.get("title", "")}
        )

        # Create or return existing favorite
        favorite, created = Favorite.objects.get_or_create(user=user, movie=movie)
        return favorite
