from django.db import models
from django.utils import timezone
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

# ==========================
#   GENRE MODEL
# ==========================
class Genre(models.Model):
    tmdb_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

# ==========================
#   MOVIE MODEL
# ==========================
class Movie(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    tmdb_id = models.IntegerField(unique=True, null=True, blank=True)
    poster_path = models.CharField(max_length=1024, blank=True, null=True)
    release_year = models.IntegerField(blank=True, null=True)
    popularity = models.FloatField(default=0.0)
    runtime = models.IntegerField(blank=True, null=True)
    vote_average = models.FloatField(default=0.0)
    vote_count = models.IntegerField(default=0)
    genres = models.ManyToManyField(Genre, related_name="movies")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

     # New fields to track live user reviews
    avg_rating = models.FloatField(default=0.0)
    review_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-popularity"]
        
        indexes = [
            models.Index(fields=["popularity"]),
            models.Index(fields=["vote_average"]),
            models.Index(fields=["tmdb_id"]),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.tmdb_id})"

      # -----------------------------
    # Properties for React frontend
    # -----------------------------

    @property
    def poster_url(self):
        """Full poster URL for React frontend."""
        if self.poster_path:
            return f"https://image.tmdb.org/t/p/w500{self.poster_path}"
        return None

    @property
    def genre_names(self):
        """Return list of genre names."""
        return list(self.genres.values_list('name', flat=True))

    @property
    def rating_summary(self):
        """Combine average rating and vote count for frontend."""
        return {
            "avg": self.vote_average,
            "count": self.vote_count
        }

    @property
    def release_year_safe(self):
        """Fallback to release_date year if release_year is missing."""
        if self.release_year:
            return self.release_year
        if self.release_date:
            return self.release_date.year
        return None

    @classmethod
    def fetch_or_create_from_tmdb(cls, tmdb_id, tmdb_data=None):
        movie, created = cls.objects.get_or_create(tmdb_id=tmdb_id)
        if created and tmdb_data:
            movie.title = tmdb_data.get("title", "")
            movie.description = tmdb_data.get("overview", "")
            movie.poster_path = tmdb_data.get("poster_path")
            movie.release_date = tmdb_data.get("release_date")
            movie.popularity = tmdb_data.get("popularity", 0.0)
            movie.vote_average = tmdb_data.get("vote_average", 0.0)
            movie.vote_count = tmdb_data.get("vote_count", 0)
            movie.save()
            # Sync genres
            for g in tmdb_data.get("genres", []):
                genre, _ = Genre.objects.get_or_create(tmdb_id=g["id"], defaults={"name": g["name"]})
                movie.genres.add(genre)
        return movie

# ==========================
#   TRENDING MOVIE
# ==========================
class TrendingMovie(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="trending_entries")
    rank = models.IntegerField()
    fetched_at = models.DateTimeField(default=timezone.now)
    score = models.FloatField(default=0)

    class Meta:
        ordering = ['rank']
        constraints = [
            models.UniqueConstraint(fields=['movie', 'fetched_at'], name='unique_trending_movie_per_fetch')
        ]

        indexes = [
            models.Index(fields=["rank"]),
            models.Index(fields=["score"]),
            models.Index(fields=["fetched_at"]),
            models.Index(fields=["movie"]),
        ]
# ==========================
#   WATCHLIST
# ==========================
class Watchlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="watchlist")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="in_watchlists")
    watched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "watchlist"
        constraints = [
            models.UniqueConstraint(fields=["user", "movie"], name="unique_user_movie_watchlist")
        ]

        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["movie"]),
            models.Index(fields=["watched_at"]),
        ]

    def __str__(self):
        return f"Watchlist: {self.user} → {self.movie}"

# ==========================
#   MOVIE VIEW LOGS 
# ==========================
class MovieViewLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="movie_view_logs")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="view_logs")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "movie_view_logs"

        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["movie"]),
            models.Index(fields=["timestamp"]),
        ]

# ==========================
#   MOVIE STATS
# ==========================
class MovieStats(models.Model):
    movie = models.OneToOneField(Movie, on_delete=models.CASCADE, related_name="stats")
    avg_rating = models.FloatField(default=0.0)
    reviews_count = models.IntegerField(default=0)
    favorites_count = models.IntegerField(default=0)
    watch_count = models.IntegerField(default=0)
    trending_score = models.FloatField(default=0.0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["avg_rating"]),
            models.Index(fields=["reviews_count"]),
            models.Index(fields=["favorites_count"]),
            models.Index(fields=["watch_count"]),
            models.Index(fields=["trending_score"]),
        ]

    def __str__(self):
        return f"MovieStats: {self.movie.title}"
    
@receiver(post_save, sender=Movie)
def create_movie_stats(sender, instance, created, **kwargs):
    if created:
        MovieStats.objects.get_or_create(movie=instance)

@receiver(post_save, sender=Watchlist)
def update_watch_count(sender, instance, **kwargs):
    """
    Update MovieStats.watch_count whenever a Watchlist entry is created.
    """
    stats, _ = MovieStats.objects.get_or_create(movie=instance.movie)
    stats.watch_count = Watchlist.objects.filter(movie=instance.movie).count()
    stats.save()
