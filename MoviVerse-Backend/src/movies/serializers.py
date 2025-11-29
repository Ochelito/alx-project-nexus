from rest_framework import serializers
from .models import Movie, TrendingMovie

class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = '__all__'

class TrendingMovieSerializer(serializers.ModelSerializer):
    movie = MovieSerializer()

    class Meta:
        model = TrendingMovie
        fields = ['movie', 'rank', 'fetched_at']
