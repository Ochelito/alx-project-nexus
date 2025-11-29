from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    preferred_genres = models.JSONField(default=list, blank=True)  # store list of tmdb genre ids
    watch_history = models.JSONField(default=list, blank=True)  # list of tmdb ids in order

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

class Recommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie_id = models.IntegerField()  # TMDb ID
    reason = models.CharField(max_length=255)
    score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'movie_id')
