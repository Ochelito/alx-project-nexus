from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import generics, permissions, serializers
from rest_framework.pagination import PageNumberPagination
from django.core.cache import cache
from django.db.models.signals import post_save
from django.dispatch import receiver
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Movie, Genre, Watchlist, MovieStats
from .serializers import (
    TMDbMovieSerializer,
    MovieSerializer,
    GenreSerializer,
    WatchlistSerializer,
    MovieStatsSerializer
)
from .services.tmdb_client import TMDbClient

tmdb = TMDbClient()


# -----------------------------
# Pagination
# -----------------------------
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


# -----------------------------
# Trending Movies (TMDb-first, cached)
# -----------------------------
@swagger_auto_schema(
    method="get",  # <- specify the HTTP method
    tags=["Movies"],
    operation_summary="Get trending movies from TMDb",
    responses={200: MovieSerializer(many=True)}
)
@api_view(["GET"])
def trending_movies(request):
    page = request.query_params.get("page", 1)
    cache_key = f"tmdb_trending_page_{page}"
    cached = cache.get(cache_key)
    if cached:
        return Response(cached)

    try:
        resp = tmdb.trending(page=page)
    except Exception as e:
        return Response({"error": f"Failed to fetch trending movies: {str(e)}"}, status=502)

    serializer = TMDbMovieSerializer(resp, many=True)
    cache.set(cache_key, serializer.data, 60 * 30)  # 30 minutes
    return Response(serializer.data)


# -----------------------------
# Search Movies (TMDb-first, cached)
# -----------------------------
@swagger_auto_schema(
    method="get",
    tags=["Movies"],
    operation_summary="Search movies globally",
    manual_parameters=[
        openapi.Parameter("query", openapi.IN_QUERY, type=openapi.TYPE_STRING)
    ],
    responses={200: MovieSerializer(many=True)}
)
@api_view(["GET"])
def search_movies(request):
    query = request.query_params.get("q")
    page = request.query_params.get("page", 1)
    if not query:
        return Response([])

    cache_key = f"tmdb_search_{query}_page_{page}"
    cached = cache.get(cache_key)
    if cached:
        return Response(cached)

    try:
        resp = tmdb.search_movies(query, page=page)
    except Exception as e:
        return Response({"error": f"Search failed: {str(e)}"}, status=502)

    serializer = TMDbMovieSerializer(resp, many=True)
    cache.set(cache_key, serializer.data, 60 * 10)  # 10 minutes
    return Response(serializer.data)


# -----------------------------
# Movie Detail (TMDb-first, DB-sync)
# -----------------------------
@swagger_auto_schema(
    method="get",
    tags=["Movies"],
    operation_summary="Get movie details by TMDb ID",
    manual_parameters=[
        openapi.Parameter("tmdb_id", openapi.IN_PATH, type=openapi.TYPE_INTEGER)
    ],
    responses={200: MovieSerializer}
)
@api_view(["GET"])
def movie_detail(request, tmdb_id):
    try:
        # Fetch TMDb data first
        tmdb_data = tmdb.movie_detail(tmdb_id)
    except Exception as e:
        return Response({"error": f"Movie not found: {str(e)}"}, status=404)

    # Sync to DB
    movie, _ = MovieSerializer.fetch_or_create(tmdb_id)
    serializer = MovieSerializer(movie)
    return Response(serializer.data)


# -----------------------------
# TMDb Genres (sync to DB, cached)
# -----------------------------
@api_view(["GET"])
def tmdb_genres(request):
    cached = cache.get("tmdb_genres")
    if cached:
        return Response(cached)

    try:
        genres = tmdb.genres()
    except Exception as e:
        return Response({"error": f"Failed to fetch genres: {str(e)}"}, status=502)

    # Sync genres to DB
    for g in genres:
        Genre.objects.get_or_create(tmdb_id=g["id"], defaults={"name": g["name"]})

    serializer = GenreSerializer(genres, many=True)
    cache.set("tmdb_genres", serializer.data, 24 * 3600)  # 24 hours
    return Response(serializer.data)


# -----------------------------
# Watchlist Views
# -----------------------------
class WatchlistCreateView(generics.CreateAPIView):
    serializer_class = WatchlistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        tmdb_id = self.request.data.get("tmdb_id")
        if not tmdb_id:
            raise serializers.ValidationError({"tmdb_id": "This field is required."})

        # Fetch or create movie from TMDb
        movie, _ = MovieSerializer.fetch_or_create(tmdb_id)
        serializer.save(user=self.request.user, movie=movie)


class WatchlistListView(generics.ListAPIView):
    serializer_class = WatchlistSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Watchlist.objects.filter(user=self.request.user).select_related("movie")


# -----------------------------
# Movie Stats
# -----------------------------
class MovieStatsListView(generics.ListAPIView):
    serializer_class = MovieStatsSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return MovieStats.objects.select_related("movie").all()


# -----------------------------
# Signals: Update watch_count
# -----------------------------
@receiver(post_save, sender=Watchlist)
def update_watch_count(sender, instance, **kwargs):
    stats, _ = MovieStats.objects.get_or_create(movie=instance.movie)
    stats.watch_count = Watchlist.objects.filter(movie=instance.movie).count()
    stats.save()
