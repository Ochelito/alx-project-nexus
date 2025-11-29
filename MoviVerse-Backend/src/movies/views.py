from rest_framework import generics, permissions
from .models import Movie, Genre, TrendingMovie
from .serializers import MovieSerializer, TrendingMovieSerializer, GenreSerializer
from rest_framework.response import Response
from rest_framework.decorators import api_view
from tmdb.client import TMDbClient
from django.core.cache import cache
from rest_framework.views import APIView
from core.utils import success, error


tmdb = TMDbClient()

class MovieListView(generics.ListAPIView):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

class MovieDetailView(generics.RetrieveAPIView):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    lookup_field = 'id'

class TrendingMoviesView(generics.ListAPIView):
    serializer_class = TrendingMovieSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return TrendingMovie.objects.select_related('movie').all()

    def get(self, request):
        movies = tmdb.get_trending()
        return Response(movies)

    def get(self, request):
        cached = cache.get("trending_movies")
        if cached:
            return success(cached)

        tmdb = TMDbClient()
        movies = tmdb.get_trending_movies()

        if movies is None:
            return error("Failed to fetch trending movies", 500)

        # Format for React frontend
        formatted = [
            {
                "id": m["id"],
                "title": m["title"],
                "poster_url": f"https://image.tmdb.org/t/p/w500{m['poster_path']}" if m.get("poster_path") else None,
                "rating": m.get("vote_average"),
                "overview": m.get("overview"),
                "release_date": m.get("release_date"),
            }
            for m in movies
        ]

        cache.set("trending_movies", formatted, 60 * 30)
        return success(formatted)

@api_view(["GET"])
def tmdb_trending(request):
    """
    Return TMDb trending directly (cached)
    """
    cached = cache.get("tmdb_trending")
    if cached:
        return Response(cached)
    client = TMDbClient()
    resp = client.trending(page=request.query_params.get("page", 1))
    cache.set("tmdb_trending", resp, timeout=60*10)  # cache 10min
    return Response(resp)

class SearchMoviesAPIView(ListAPIView):
    serializer_class = MovieSerializer
    pagination_class = PageNumberPagination

    def get_queryset(self):
        query = self.request.query_params.get("q", "")
        return Movie.objects.filter(title__icontains=query)

class SearchView(APIView):
    def get(self, request):
        query = request.GET.get("q", "")
        if not query:
            return Response({"results": []})
        return Response(tmdb.search_movies(query))
    
class MovieDetail(generics.RetrieveAPIView):
    lookup_field = "tmdb_id"
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    permission_classes = [permissions.AllowAny]

@api_view(["GET"])
def search(request):
    q = request.query_params.get("q")
    page = request.query_params.get("page", 1)
    if not q:
        return Response({"results": []})
    client = TMDbClient()
    resp = client.search_movie(q, page=page)
    return Response(resp)

@api_view(["GET"])
def genres(request):
    cached = cache.get("tmdb_genres")
    if cached:
        return Response(cached)
    client = TMDbClient()
    resp = client.genres()
    cache.set("tmdb_genres", resp, timeout=24*3600)
    return Response(resp)
