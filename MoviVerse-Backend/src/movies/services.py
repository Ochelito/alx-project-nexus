from .models import Movie, MovieViewLog, TrendingMovie
from favorites.models import Favorite
from math import log
from django.utils import timezone
from datetime import timedelta


def compute_trending_for_period(period="weekly", top_n=100):
    """
    Compute trending movies based on views, favorites, and TMDb ID as a tie-breaker.
    Saves top N movies into TrendingMovie table.
    """
    now = timezone.now()
    window = now - timedelta(days=7)  # last 7 days

    movies = Movie.objects.all()
    trending_items = []

    for movie in movies:
        views = MovieViewLog.objects.filter(
            movie=movie, timestamp__gte=window
        ).count()

        favs = Favorite.objects.filter(movie=movie).count()

        score = (
            log(1 + views) * 0.6 +
            log(1 + favs) * 1.2 +
            (movie.tmdb_id or 0) * 0.01
        )

        trending_items.append((score, movie))

    trending_items.sort(reverse=True, key=lambda i: i[0])

    # clear existing trending entries
    TrendingMovie.objects.filter(fetched_at__gte=window).delete()

    for rank, (score, movie) in enumerate(trending_items[:top_n], start=1):
        TrendingMovie.objects.update_or_create(
            movie=movie,
            fetched_at=timezone.now(),
            defaults={"rank": rank, "score": score}
        )
