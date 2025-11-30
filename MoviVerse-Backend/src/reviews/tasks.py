from celery import shared_task
from django.db.models import Avg, Count
from movies.models import Movie
from .models import Review

@shared_task
def update_movie_rating(tmdb_id):
    """
    Recalculate the average rating and review count for a movie.
    This task should be triggered whenever a review is added, updated, or deleted.
    """
    try:
        movie = Movie.objects.get(tmdb_id=tmdb_id)
    except Movie.DoesNotExist:
        return f"Movie with TMDb ID {tmdb_id} does not exist."

    agg = Review.objects.filter(movie=movie).aggregate(
        avg_rating=Avg("rating"),
        review_count=Count("id")
    )

    movie.avg_rating = agg["avg_rating"] or 0
    movie.review_count = agg["review_count"]
    movie.save(update_fields=["avg_rating", "review_count"])

    return f"Updated movie {movie.title} (TMDb ID: {tmdb_id}) with avg_rating={movie.avg_rating} and review_count={movie.review_count}"
