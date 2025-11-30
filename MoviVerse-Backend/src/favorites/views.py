from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from movies.models import Movie
from .models import Favorite
from .serializers import FavoriteSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# -----------------------------
# List Favorites
# -----------------------------
class FavoriteListView(generics.ListAPIView):
    """
    Lists all favorite movies for the authenticated user.
    """
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="List all favorite movies for the authenticated user",
        responses={200: FavoriteSerializer(many=True)}
    )

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).select_related("movie")


# -----------------------------
# Add Favorite
# -----------------------------
class AddFavoriteAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Add a movie to user's favorites",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["tmdb_id"],
            properties={
                "tmdb_id": openapi.Schema(type=openapi.TYPE_INTEGER, description="TMDb ID of the movie"),
                "title": openapi.Schema(type=openapi.TYPE_STRING, description="Optional movie title if new")
            }
        ),
        responses={200: openapi.Response(description="Movie added to favorites")}
    )

    def post(self, request):
        tmdb_id = request.data.get("tmdb_id")
        if not tmdb_id:
            return Response({"detail": "tmdb_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        movie, _ = Movie.objects.get_or_create(tmdb_id=tmdb_id, defaults={"title": request.data.get("title", "")})
        favorite, created = Favorite.objects.get_or_create(user=request.user, movie=movie)

        return Response({
            "created": created,
            "movie_id": movie.tmdb_id,
            "title": movie.title
        })


# -----------------------------
# Remove Favorite
# -----------------------------
class RemoveFavoriteAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Remove a movie from user's favorites",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["tmdb_id"],
            properties={
                "tmdb_id": openapi.Schema(type=openapi.TYPE_INTEGER, description="TMDb ID of the movie")
            }
        ),
        responses={200: openapi.Response(description="Movie removed from favorites")}
    )

    def post(self, request):
        tmdb_id = request.data.get("tmdb_id")
        if not tmdb_id:
            return Response({"detail": "tmdb_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            movie = Movie.objects.get(tmdb_id=tmdb_id)
        except Movie.DoesNotExist:
            return Response({"detail": "Movie not found"}, status=status.HTTP_404_NOT_FOUND)

        deleted, _ = Favorite.objects.filter(user=request.user, movie=movie).delete()
        return Response({"removed": bool(deleted)})


# -----------------------------
# Optional function-based endpoints
# -----------------------------
@swagger_auto_schema(
    method="get",
    operation_summary="Get formatted favorites list for user",
    responses={200: openapi.Response(description="List of favorite movies")}
)
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def list_favorites(request):
    """
    Returns a formatted list of favorites for the user.
    """
    favorites = Favorite.objects.filter(user=request.user).select_related("movie")
    response = [
        {
            "movie_id": f.movie.tmdb_id,
            "title": f.movie.title,
            "poster_url": f"https://image.tmdb.org/t/p/w500{f.movie.poster_path}" if f.movie.poster_path else None,
        }
        for f in favorites
    ]
    return Response(response)
