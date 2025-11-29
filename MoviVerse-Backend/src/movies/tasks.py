import requests
from celery import shared_task
from django.conf import settings
from .models import Movie, TrendingMovie
from django.utils import timezone

TMDB_API_KEY = settings.TMDB_API_KEY
TMDB_BASE_URL = "https://api.themoviedb.org/3"

@shared_task
def fetch_trending_movies():
    url = f"{TMDB_BASE_URL}/trending/movie/week?api_key={TMDB_API_KEY}"
    response = requests.get(url)
    if response.status_code != 200:
        return []

    data = response.json().get('results', [])
    TrendingMovie.objects.all().delete()  # Clear old trending data

    for rank, item in enumerate(data, start=1):
        movie, created = Movie.objects.get_or_create(
            tmdb_id=item['id'],
            defaults={
                'title': item['title'],
                'description': item.get('overview'),
                'release_year': int(item.get('release_date', '0000')[:4]) if item.get('release_date') else None,
                'poster_path': item.get('poster_path'),
                'genre': ','.join(str(gid) for gid in item.get('genre_ids', []))
            }
        )
        TrendingMovie.objects.create(
            movie=movie,
            rank=rank,
            fetched_at=timezone.now()
        )
