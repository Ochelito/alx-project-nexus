from celery import shared_task
from django.db import transaction
from .models import Movie, Genre, MovieStats, Review, Favorite, WatchEvent, Recommendation
from core.tmdb_client import TMDbClient
from django.contrib.auth import get_user_model
from django.db.models import Avg, Count
from math import log
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

@shared_task
def sync_tmdb_popular(pages=2):
    client = TMDbClient()
    for page in range(1, pages + 1):
        data = client.popular(page=page)
        results = data.get("results", [])
        for item in results:
            movie, _ = Movie.objects.update_or_create(
                tmdb_id=item["id"],
                defaults={
                    "title": item.get("title") or item.get("name"),
                    "overview": item.get("overview"),
                    "poster_path": item.get("poster_path"),
                    "release_date": item.get("release_date") or None,
                    "popularity": item.get("popularity") or 0.0,
                    "vote_average": item.get("vote_average") or 0.0,
                    "vote_count": item.get("vote_count") or 0,
                    "is_active": True,
                },
            )
    return {"ok": True}

@shared_task
def recompute_movie_stats_and_trending():
    """
    Recompute MovieStats (avg rating, counts) and trending score based on recent activity.
    """
    seven_days_ago = timezone.now() - timedelta(days=7)
    for movie in Movie.objects.all():
        avg_rating = Review.objects.filter(movie=movie).aggregate(avg=Avg("rating"))["avg"] or 0.0
        reviews_count = Review.objects.filter(movie=movie).count()
        favorites_count = Favorite.objects.filter(movie=movie).count()
        watch_count = WatchEvent.objects.filter(movie=movie).count()

        # Simple trending formula: weight recent interactions higher (example)
        recent_views = WatchEvent.objects.filter(movie=movie, watched_at__gte=seven_days_ago).count()
        recent_favs = Favorite.objects.filter(movie=movie, created_at__gte=seven_days_ago).count()
        recent_reviews = Review.objects.filter(movie=movie, created_at__gte=seven_days_ago).count()
        # Normalise
        trending_score = (
            (log(1 + recent_views) * 0.6) +
            (log(1 + recent_favs) * 1.2) +
            (log(1 + recent_reviews) * 1.0) +
            (movie.popularity * 0.2)
        )

        stats, _ = MovieStats.objects.get_or_create(movie=movie)
        stats.avg_rating = avg_rating
        stats.reviews_count = reviews_count
        stats.favorites_count = favorites_count
        stats.watch_count = watch_count
        stats.trending_score = trending_score
        stats.save()
    return {"ok": True}

@shared_task
def compute_recommendations_for_all_users(limit_per_user=20):
    """
    Very practical hybrid recommender:
    - For each user take their favorites and highly rated movies
    - Recommend movies that share genres and are popular but not yet favorited or reviewed by user
    """
    users = User.objects.all()
    for user in users:
        favorites = Favorite.objects.filter(user=user).select_related("movie")
        liked_movie_ids = [f.movie.id for f in favorites]

        # Gather candidate movies: same genres as favorites
        candidate_qs = Movie.objects.filter(is_active=True)
        if liked_movie_ids:
            fav_genres = Genre.objects.filter(movies__id__in=liked_movie_ids).values_list("id", flat=True)
            candidate_qs = candidate_qs.filter(genres__in=fav_genres).distinct()

        # Remove user's already interacted movies
        candidate_qs = candidate_qs.exclude(id__in=liked_movie_ids)
        # Score = genre matches count * popularity factor
        scored = []
        for m in candidate_qs[:500]:  # limit scanning
            common_genres = m.genres.filter(id__in=fav_genres).count() if liked_movie_ids else 0
            score = common_genres * 1.0 + (m.popularity or 0.0) * 0.1
            scored.append((score, m))

        scored.sort(reverse=True, key=lambda x: x[0])
        # Upsert top N recommendations for user
        Recommendation.objects.filter(user=user).delete()
        for score, movie in scored[:limit_per_user]:
            Recommendation.objects.create(user=user, movie=movie, score=score, reason="genre + popularity")
    return {"ok": True}
