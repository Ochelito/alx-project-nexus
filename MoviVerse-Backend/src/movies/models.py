from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone


# ==========================
#   USER MODEL (MERGED)
#   - keeps email, username, timestamps from SQL
#   - uses Django password system (not password_hash)
# ==========================
class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, max_length=255)
    username = models.CharField(unique=True, max_length=50)
    password = models.CharField(max_length=255)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.username


# ==========================
#   GENRE MODEL (UPGRADED)
#   - replaces the simple "genre VARCHAR" from SQL
# ==========================
class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    tmdb_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "genres"

    def __str__(self):
        return self.name


# ==========================
#   MOVIE MODEL
#   - keeps title, description, release_year from SQL
#   - upgrades genres into many-to-many
#   - adds tmdb_id, metadata fields
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
    genres = models.ManyToManyField(Genre, related_name="movies")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "movies"

    def __str__(self):
        return f"{self.title} ({self.tmdb_id})"


# ==========================
#   REVIEW MODEL
#   - matches SQL: rating, review_text, unique (user, movie)
# ==========================
class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="reviews")

    rating = models.IntegerField()
    review_text = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reviews"
        unique_together = ("user", "movie")

    def __str__(self):
        return f"{self.user.username} → {self.movie.title} ({self.rating})"


# ==========================
#   FAVORITES MODEL
#   - matches SQL schema exactly
#   - keeps unique (user, movie)
# ==========================
class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorites")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="favorited_by")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "favorites"
        unique_together = ("user", "movie")

    def __str__(self):
        return f"{self.user.username} ❤️ {self.movie.title}"


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
#   RECOMMENDATIONS
#   - keeps reason + unique constraint from SQL schema
# ==========================
class Recommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recommendations")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="recommended_to")
    reason = models.CharField(max_length=255, null=True, blank=True)
    score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "recommendations"
        unique_together = ("user", "movie")

    def __str__(self):
        return f"Recommendation → {self.user.username}: {self.movie.title}"


# ==========================
#   MOVIE VIEW LOGS (new)
# ==========================
class MovieViewLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="view_logs")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="view_logs")
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "movie_view_logs"


# ==========================
#   TRENDING MOVIES (new)
# ==========================
class TrendingMovie(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    score = models.FloatField(default=0)
    period = models.CharField(max_length=20, default="daily")

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "trending_movies"
        unique_together = ("movie", "period")

class MovieStats(models.Model):
    movie = models.OneToOneField(Movie, on_delete=models.CASCADE, related_name="stats")
    avg_rating = models.FloatField(default=0.0)
    reviews_count = models.IntegerField(default=0)
    favorites_count = models.IntegerField(default=0)
    watch_count = models.IntegerField(default=0)
    trending_score = models.FloatField(default=0.0)
    updated_at = models.DateTimeField(auto_now=True)
