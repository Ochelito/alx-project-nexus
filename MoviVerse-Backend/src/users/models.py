from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.conf import settings

User = settings.AUTH_USER_MODEL

class User(AbstractUser):
    email = models.EmailField(unique=True)
    
    # Store preferred genres as TMDb IDs (list of ints)
    preferred_genres = models.JSONField(default=list, blank=True)
    
    # Store watch history as TMDb IDs (list of ints, most recent first)
    watch_history = models.JSONField(default=list, blank=True)
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def add_to_watch_history(self, tmdb_id: int):
        """Add movie to watch history (most recent first, no duplicates)."""
        if tmdb_id in self.watch_history:
            self.watch_history.remove(tmdb_id)
        self.watch_history.insert(0, tmdb_id)
        # Optional: limit history length
        self.watch_history = self.watch_history[:200]
        self.save(update_fields=['watch_history'])

    def set_preferred_genres(self, genre_ids: list):
        """Update user's preferred genres."""
        self.preferred_genres = list(set(genre_ids))  # remove duplicates
        self.save(update_fields=['preferred_genres'])

    def clear_recommendations(self):
        """Delete all previous recommendations for fresh computation."""
        self.recommendations.all().delete()

    def add_recommendation(self, movie_id: int, reason: str, score: float = 0.0):
        """Add a single recommendation for the user."""
        Recommendation.objects.update_or_create(
            user=self,
            movie_id=movie_id,
            defaults={'reason': reason, 'score': score, 'created_at': timezone.now()}
        )


class Recommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recommendations")
    movie_id = models.IntegerField()  # TMDb ID
    reason = models.CharField(max_length=255)
    score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'movie_id')
        ordering = ['-score', '-created_at']

    def __str__(self):
        return f"{self.user.email} → {self.movie_id} ({self.reason})"

