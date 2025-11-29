from rest_framework import generics, permissions
from .models import User, Recommendation
from .serializers import UserSerializer, RecommendationSerializer, RegisterSerializer
from .permissions import IsOwnerOrReadOnly
from tmdb.client import TMDbClient
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from favorites.models import Favorite
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

tmdb = TMDbClient()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer, RegisterSerializer
    permission_class = [permissions.AllowAny]

class LoginAPIView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        user = authenticate(email=email, password=password)
        if not user:
            return error("Invalid login credentials", 401)

        refresh = RefreshToken.for_user(user)
        return success({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "email": user.email
            }
        })

class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

class RecommendationListView(generics.ListAPIView):
    serializer_class = RecommendationSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get(self, request):
        # Simple genre-based recommendation from favorite genres
        rec_movies = []
        genres = request.user.favorite_genres or []
        for movie in tmdb.get_trending():
            if any(g in movie.get("genre_ids", []) for g in genres):
                rec_movies.append(movie)
        # mark if favorite
        user_favs = set(Favorite.objects.filter(user=request.user).values_list("tmdb_id", flat=True))
        for m in rec_movies:
            m["is_favorite"] = m["id"] in user_favs
        return Response(rec_movies)

    def get_queryset(self):
        return Recommendation.objects.filter(user=self.request.user)

    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return error("Authentication required", 401)

        tmdb = TMDbClient()
        movies = tmdb.get_recommendations_for_user(user)

        formatted = [
            {
                "id": m["id"],
                "title": m["title"],
                "poster_url": f"https://image.tmdb.org/t/p/w500{m['poster_path']}",
                "rating": m["vote_average"],
            }
            for m in movies
        ]

        return success(formatted)

@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def recommendations(request):
    """
    Basic hybrid recommendation:
    1. Use watch_history top genres (if present)
    2. Fallback to TMDb trending
    """
    user = request.user
    client = TMDbClient()
    # simple genre based: take preferred_genres first
    if user.preferred_genres:
        # Use Discover? but to keep simple use /search by genre not allowed here. We'll return TMDb recommendations using genres via discover endpoint
        try:
            resp = client._get("/discover/movie", {"with_genres": ",".join(map(str, user.preferred_genres)), "sort_by": "vote_average.desc", "page": 1})
            return Response(resp)
        except Exception:
            pass

    # fallback
    resp = client.trending()
    return Response(resp)
