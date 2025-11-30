from django.db import models
from django.conf import settings
from movies.models import Movie
from rest_framework import serializers

class MovieBasicSerializer(serializers.ModelSerializer):
    """
    Simple serializer for movie details nested in favorites.
    """
    class Meta:
        model = Movie
        fields = ["tmdb_id", "title", "poster_path", "vote_average"]

class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorites"
    )
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "movie")  # Each user can favorite a movie only once
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} - {self.movie.title}"
