from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Review
from .tasks import update_movie_rating

@receiver(post_save, sender=Review)
def review_saved(sender, instance, **kwargs):
    # Update movie rating whenever a review is created or updated
    update_movie_rating.delay(instance.movie.tmdb_id)

@receiver(post_delete, sender=Review)
def review_deleted(sender, instance, **kwargs):
    # Update movie rating whenever a review is deleted
    update_movie_rating.delay(instance.movie.tmdb_id)
