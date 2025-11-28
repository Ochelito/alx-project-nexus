from django.db import models
from django.db import models
from django.conf import settings


User = settings.AUTH_USER_MODEL

# Create your models here.
class Genre(models.Model):
    name = models.CharField(max_length=120, unique=True)
    tmdb_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Movie(models.Model):
    tmdb_id = models.IntegerField(unique=True, db_index=True)
    title = models.CharField(max_length=512, db_index=True)
    overview = models.TextField(blank=True, null=True)
    poster_path = models.CharField(max_length=1024, blank=True, null=True)
    release_date = models.DateField(blank=True, null=True)
    runtime = models.IntegerField(blank=True, null=True)
    popularity = models.FloatField(default=0.0)
    vote_average = models.FloatField(default=0.0)
    vote_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    genres = models.ManyToManyField(Genre, related_name="movies", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.tmdb_id})"

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField()  # 1..10
    text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "movie")

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorites")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="favorites")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "movie")

class WatchEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="watch_events")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="watch_events")
    watched_at = models.DateTimeField(auto_now_add=True)

class Recommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recommendations")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="recommended_movie")
    reason = models.CharField(max_length=255, blank=True)
    score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "movie")

class MovieStats(models.Model):
    movie = models.OneToOneField(Movie, on_delete=models.CASCADE, related_name="stats")
    avg_rating = models.FloatField(default=0.0)
    reviews_count = models.IntegerField(default=0)
    favorites_count = models.IntegerField(default=0)
    watch_count = models.IntegerField(default=0)
    trending_score = models.FloatField(default=0.0)
    updated_at = models.DateTimeField(auto_now=True)
