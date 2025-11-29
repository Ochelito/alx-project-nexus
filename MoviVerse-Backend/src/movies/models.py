from django.db import models
from django.utils import timezone

# ==========================
#   MOVIE MODEL
# ==========================
class Movie(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    release_year = models.IntegerField(null=True, blank=True)
    tmdb_id = models.IntegerField(unique=True, null=True, blank=True)
    overview = models.TextField(blank=True, null=True)
    poster_path = models.CharField(max_length=1024, blank=True, null=True)
    release_date = models.DateField(blank=True, null=True)
    popularity = models.FloatField(default=0.0)
    runtime = models.IntegerField(blank=True, null=True)
    vote_average = models.FloatField(default=0.0)
    vote_count = models.IntegerField(default=0)
    genres = models.ManyToManyField(Genre, related_name="movies")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-popularity"]

    def __str__(self):
        return f"{self.title} ({self.tmdb_id})"

class Genre(models.Model):
    tmdb_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class TrendingMovie(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    rank = models.IntegerField()
    fetched_at = models.DateTimeField(default=timezone.now)
    score = models.FloatField(default=0)

    class Meta:
        ordering = ['rank']
        unique_together = ('movie', 'fetched_at')


# ==========================
#   WATCHLIST (new feature)
# ==========================
class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="watchlist")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="in_watchlists")
    watched_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "watchlist"
        unique_together = ("user", "movie")


# ==========================
#   MOVIE VIEW LOGS (new)
# ==========================
class MovieViewLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="view_logs")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="view_logs")
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "movie_view_logs"


class MovieStats(models.Model):
    movie = models.OneToOneField(Movie, on_delete=models.CASCADE, related_name="stats")
    avg_rating = models.FloatField(default=0.0)
    reviews_count = models.IntegerField(default=0)
    favorites_count = models.IntegerField(default=0)
    watch_count = models.IntegerField(default=0)
    trending_score = models.FloatField(default=0.0)
    updated_at = models.DateTimeField(auto_now=True)
