from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, permission_classes
from .models import User, Recommendation
from .serializers import UserSerializer, RegisterSerializer, RecommendationSerializer
from .permissions import IsOwnerOrReadOnly
from movies.models import Movie
from favorites.models import Favorite
from users.services import compute_recommendations_for_user
from tmdb.client import TMDbClient
import logging
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

tmdb = TMDbClient()
logger = logging.getLogger(__name__)

# -----------------------------
# User Registration
# -----------------------------
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary="Register a new user",
        request_body=RegisterSerializer,
        responses={201: UserSerializer, 400: "Bad Request"}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    
# -----------------------------
# User Login
# -----------------------------
class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary="Login a user and obtain JWT tokens",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["email", "password"],
            properties={
                "email": openapi.Schema(type=openapi.TYPE_STRING),
                "password": openapi.Schema(type=openapi.TYPE_STRING)
            },
        ),
        responses={
            200: openapi.Response(
                description="JWT tokens and user info",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "access": openapi.Schema(type=openapi.TYPE_STRING),
                        "refresh": openapi.Schema(type=openapi.TYPE_STRING),
                        "user": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "email": openapi.Schema(type=openapi.TYPE_STRING),
                                "username": openapi.Schema(type=openapi.TYPE_STRING)
                            }
                        )
                    }
                )
            ),
            401: "Invalid credentials"
        }
    )

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        user = authenticate(email=email, password=password)

        if not user:
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username
            }
        })

# -----------------------------
# Current User
# -----------------------------
class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get current authenticated user details",
        responses={200: UserSerializer}
    )

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

# -----------------------------
# User Recommendations
# -----------------------------
class RecommendationListView(generics.ListAPIView):
    """
    Returns recommendations for the authenticated user.
    1. Uses locally precomputed recommendations from Recommendation table.
    2. Marks favorites.
    3. Falls back to TMDb trending if no local recommendations.
    """
    serializer_class = RecommendationSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    @swagger_auto_schema(
        operation_summary="List recommendations for authenticated user",
        responses={200: RecommendationSerializer(many=True)}
    )

    def get_queryset(self):
        # Return precomputed recommendations
        return Recommendation.objects.filter(user=self.request.user).order_by("-score")

    def list(self, request, *args, **kwargs):
        user = request.user
        recommendations = self.get_queryset()
        response_data = []

        if recommendations.exists():
            # Map movie_id to Recommendation
            rec_map = {r.movie_id: r for r in recommendations}
            movie_ids = [r.movie_id for r in recommendations]
            movies_qs = Movie.objects.filter(tmdb_id__in=movie_ids)
            user_favs = set(Favorite.objects.filter(user=user).values_list("tmdb_id", flat=True))

            for movie in movies_qs:
                r = rec_map.get(movie.tmdb_id)
                response_data.append({
                    "id": movie.tmdb_id,
                    "title": movie.title,
                    "poster_url": f"https://image.tmdb.org/t/p/w500{movie.poster_path}" if movie.poster_path else None,
                    "rating": movie.vote_average,
                    "reason": r.reason if r else "Recommended",
                    "is_favorite": movie.tmdb_id in user_favs
                })
        else:
            # Fallback to TMDb trending
            try:
                trending = tmdb.trending()
            except Exception as e:
                logger.error(f"TMDb trending fetch failed: {e}")
                trending = []

            user_favs = set(Favorite.objects.filter(user=user).values_list("tmdb_id", flat=True))
            for movie in trending:
                response_data.append({
                    "id": movie.get("id"),
                    "title": movie.get("title"),
                    "poster_url": f"https://image.tmdb.org/t/p/w500{movie.get('poster_path')}" if movie.get("poster_path") else None,
                    "rating": movie.get("vote_average"),
                    "reason": "Trending",
                    "is_favorite": movie.get("id") in user_favs
                })

        return Response(response_data)


@swagger_auto_schema(
    method='get',
    operation_summary="Fetch recommendations (fallbacks to trending if none precomputed)",
    responses={200: RecommendationSerializer(many=True)}
)
# -----------------------------
# Separate API endpoint for dynamic TMDb recommendations (optional)
# -----------------------------
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def tmdb_recommendations(request):
    """
    Returns TMDb-powered recommendations for the authenticated user using preferred_genres.
    Fallback to trending if no preferred_genres set.
    """
    user = request.user
    client = TMDbClient()

    try:
        if user.preferred_genres:
            resp = client._get(
                "/discover/movie",
                {
                    "with_genres": ",".join(map(str, user.preferred_genres)),
                    "sort_by": "vote_average.desc",
                    "page": 1
                }
            )
        else:
            resp = client.trending()
    except Exception as e:
        logger.error(f"TMDb recommendations fetch failed: {e}")
        resp = []

    # Mark favorites
    user_favs = set(Favorite.objects.filter(user=user).values_list("tmdb_id", flat=True))
    formatted = []
    for m in resp:
        formatted.append({
            "id": m.get("id"),
            "title": m.get("title"),
            "poster_url": f"https://image.tmdb.org/t/p/w500{m.get('poster_path')}" if m.get("poster_path") else None,
            "rating": m.get("vote_average"),
            "is_favorite": m.get("id") in user_favs
        })
    return Response(formatted)
