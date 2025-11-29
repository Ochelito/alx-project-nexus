from rest_framework import serializers
from .models import FavoriteItem
from movies.serializers import MovieSerializer

class FavoriteItemSerializer(serializers.ModelSerializer):
    movie = MovieSerializer(read_only=True)

    class Meta:
        model = FavoriteItem
        fields = ("id", "movie", "created_at")
