from .models import Movie, Favorite, MovieViewLog, TrendingMovie, Recommendation, Genre
from django.db.models import Count
from math import log
from django.utils import timezone
from datetime import timedelta

def compute_trending_for_period(period="weekly"):
    # simple example: last 7 days
    now = timezone.now()
    window = now - timedelta(days=7)
    movies = Movie.objects.all()
    trending_items = []
    for m in movies:
        views = MovieViewLog.objects.filter(movie=m, timestamp__gte=window).count()
        favs = Favorite.objects.filter(movie=m).count()
        score = log(1 + views) * 0.6 + log(1 + favs) * 1.2 + (m.tmdb_id or 0) * 0.01
        trending_items.append((score, m))
    trending_items.sort(reverse=True, key=lambda x: x[0])
    # upsert top 100
    TrendingMovie.objects.filter(period=period).delete()
    for score, movie in trending_items[:100]:
        TrendingMovie.objects.create(movie=movie, score=score, period=period)


def compute_recommendations_for_user(user, limit=20):
    # Very simple genre-based + popularity algorithm
    fav_movie_ids = Favorite.objects.filter(user=user).values_list("movie_id", flat=True)
    if not fav_movie_ids:
        # fallback popular movies
        candidates = Movie.objects.order_by("-id")[:limit]
        Recommendation.objects.filter(user=user).delete()
        for m in candidates:
            Recommendation.objects.create(user=user, movie=m, reason="popular")
        return

    fav_genres = Genre.objects.filter(movies__id__in=fav_movie_ids).distinct()
    candidate_qs = Movie.objects.filter(genres__in=fav_genres).exclude(id__in=fav_movie_ids).distinct()
    scored = []
    for m in candidate_qs[:500]:
        common_genres = m.genres.filter(id__in=fav_genres.values_list("id", flat=True)).count()
        score = common_genres * 1.0 + (m.tmdb_id or 0) * 0.001
        scored.append((score, m))
    scored.sort(reverse=True, key=lambda x: x[0])
    Recommendation.objects.filter(user=user).delete()
    for score, m in scored[:limit]:
        Recommendation.objects.create(user=user, movie=m, reason="genre-match")
