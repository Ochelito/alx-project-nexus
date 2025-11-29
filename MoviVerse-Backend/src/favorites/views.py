from rest_framework import generics, permissions, status
from .models import FavoriteItem, Favorite
from .serializers import FavoriteItemSerializer
from rest_framework.response import Response
from movies.models import Movie
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView

class FavoritesList(generics.ListAPIView):
    serializer_class = FavoriteItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FavoriteItem.objects.filter(user=self.request.user).select_related("movie")

    def get(self, request):
        favs = Favorite.objects.filter(user=request.user)
        return Response([f.tmdb_id for f in favs])

class AddFavoriteAPIView(APIView):
    def post(self, request):
        user = request.user
        movie_id = request.data.get("movie_id")

        if not movie_id:
            return error("movie_id is required")

        Favorite.objects.get_or_create(user=user, movie_id=movie_id)
        return success({"message": "Added to favorites"})


class RemoveFavoriteAPIView(APIView):
    def post(self, request):
        user = request.user
        movie_id = request.data.get("movie_id")

        Favorite.objects.filter(user=user, movie_id=movie_id).delete()
        return success({"message": "Removed from favorites"})


class ListFavoritesAPIView(APIView):
    def get(self, request):
        favorites = Favorite.objects.filter(user=request.user)

        formatted = [
            {
                "movie_id": f.movie_id,
                "title": f.title,
                "poster_url": f.poster_url,
            }
            for f in favorites
        ]

        return success(formatted)

@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def add_favorite(request):
    tmdb_id = request.data.get("tmdb_id")
    if not tmdb_id:
        return Response({"detail": "tmdb_id required"}, status=status.HTTP_400_BAD_REQUEST)
    movie, _ = Movie.objects.get_or_create(tmdb_id=tmdb_id, defaults={"title": request.data.get("title", "")})
    fav, created = FavoriteItem.objects.get_or_create(user=request.user, movie=movie)
    return Response({"created": created})

@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def remove_favorite(request):
    tmdb_id = request.data.get("tmdb_id")
    if not tmdb_id:
        return Response({"detail": "tmdb_id required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        movie = Movie.objects.get(tmdb_id=tmdb_id)
    except Movie.DoesNotExist:
        return Response({"detail": "movie not found"}, status=status.HTTP_404_NOT_FOUND)
    FavoriteItem.objects.filter(user=request.user, movie=movie).delete()
    return Response({"removed": True})
