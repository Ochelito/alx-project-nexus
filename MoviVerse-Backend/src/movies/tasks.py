import requests
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from movies.trending import compute_trending_for_period
from .models import Movie, Genre, TrendingMovie
from .services.tmdb_client import TMDbClient

tmdb = TMDbClient()
TMDB_API_KEY = settings.TMDB_API_KEY
CACHE_KEY = "trending_movies"
CACHE_TIMEOUT = 60 * 30  # 30 minutes

@shared_task
def fetch_trending_movies():
    """
    Fetch TMDb weekly trending movies, sync with DB, and cache results.
    """
    try:
        data = tmdb.trending(page=1)
    except Exception as e:
        print(f"[fetch_trending_movies] Failed to fetch trending movies: {e}")
        return []

    results = data.get("results", [])
    fetched_at = timezone.now()
    cached_list = []

    for rank, item in enumerate(results, start=1):
        tmdb_id = item["id"]

        # Fetch or create Movie
        movie, created = Movie.objects.update_or_create(
            tmdb_id=tmdb_id,
            defaults={
                "title": item.get("title") or item.get("name") or "",
                "description": item.get("overview", ""),
                "poster_path": item.get("poster_path"),
                "popularity": item.get("popularity", 0.0),
                "vote_average": item.get("vote_average", 0.0),
                "vote_count": item.get("vote_count", 0),
                "release_year": int(item.get("release_date")[:4]) if item.get("release_date") else None,
            }
        )

        # Sync genres
        genre_ids = item.get("genre_ids", [])
        for gid in genre_ids:
            genre, _ = Genre.objects.get_or_create(tmdb_id=gid, defaults={"name": str(gid)})
            movie.genres.add(genre)

        # Update or create trending record
        TrendingMovie.objects.update_or_create(
            movie=movie,
            fetched_at=fetched_at,
            defaults={"rank": rank, "score": item.get("popularity", 0.0)}
        )

        movie.save()

        # Prepare cache-ready data
        cached_list.append({
            "tmdb_id": movie.tmdb_id,
            "title": movie.title,
            "poster_url": movie.poster_url,
            "vote_average": movie.vote_average,
            "vote_count": movie.vote_count,
            "genres": movie.genre_names,
            "popularity": movie.popularity,
            "rank": rank
        })

    # Set cache
    cache.set(CACHE_KEY, cached_list, CACHE_TIMEOUT)
    print(f"[fetch_trending_movies] Synced and cached {len(results)} trending movies.")

@shared_task
def generate_trending():
    compute_trending_for_period(period="weekly", top_n=100)
