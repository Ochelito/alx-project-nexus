from rest_framework import serializers
from .models import Review
from movies.serializers import MovieSerializer
from movies.models import Movie

class ReviewSerializer(serializers.ModelSerializer):
    movie = MovieSerializer(read_only=True)
    movie_id = serializers.IntegerField(write_only=True)  # frontend will send this

    class Meta:
        model = Review
        fields = ["id", "user", "movie", "movie_id", "rating", "comment", "created_at", "updated_at"]
        read_only_fields = ["id", "user", "movie", "created_at", "updated_at"]

    def create(self, validated_data):
        user = self.context["request"].user
        movie_id = validated_data.pop("movie_id")
        movie = Movie.objects.get(tmdb_id=movie_id)
        review, created = Review.objects.update_or_create(
            user=user,
            movie=movie,
            defaults=validated_data
        )
        return review

    def update(self, instance, validated_data):
        """
        Optional: allow users to update rating/comment.
        """
        instance.rating = validated_data.get("rating", instance.rating)
        instance.comment = validated_data.get("comment", instance.comment)
        instance.save()
        return instance
