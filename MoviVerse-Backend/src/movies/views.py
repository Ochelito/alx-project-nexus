from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Count
from django.utils import timezone
from datetime import timedelta

from .models import Movie, Genre, Review, Favorite, Recommendation, Watchlist, MovieViewLog, TrendingMovie
from .serializers import (
    MovieSerializer, MovieCreateUpdateSerializer, GenreSerializer,
    ReviewSerializer, FavoriteSerializer, RecommendationSerializer,
    WatchlistSerializer, TrendingMovieSerializer
)
from .permissions import IsOwnerOrReadOnly
from rest_framework.generics import CreateAPIView
from .serializers import RegisterSerializer

# ---------- User Registration ----------
class RegisterView(CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

# ---------- Movie ViewSet ----------
class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.filter()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "description"]
    ordering_fields = ["release_year", "created_at"]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return MovieCreateUpdateSerializer
        return MovieSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAuthenticated()]  # restrict to authenticated (admin/staff ideally)
        return [AllowAny()]

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        movie = self.get_object()
        fav, created = Favorite.objects.get_or_create(user=request.user, movie=movie)
        serializer = FavoriteSerializer(fav)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def watch(self, request, pk=None):
        movie = self.get_object()
        # Log a view
        MovieViewLog.objects.create(user=request.user, movie=movie)
        # Optionally add to watchlist or mark watched - here just a log
        return Response({"ok": True}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], permission_classes=[AllowAny])
    def trending(self, request):
        # Simple: return top TrendingMovie entries
        qs = TrendingMovie.objects.select_related("movie").order_by("-score")[:50]
        serializer = TrendingMovieSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def recommendations(self, request):
        qs = Recommendation.objects.filter(user=request.user).select_related("movie").order_by("-created_at")
        serializer = RecommendationSerializer(qs, many=True)
        return Response(serializer.data)


# ---------- Genre ViewSet ----------
class GenreViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [AllowAny]


# ---------- Review ViewSet ----------
class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.select_related("user", "movie").all().order_by("-created_at")
    serializer_class = ReviewSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# ---------- Favorite ViewSet (optional) ----------
class FavoriteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Favorite.objects.select_related("user", "movie").all()
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]


# ---------- Watchlist ViewSet ----------
class WatchlistViewSet(viewsets.ModelViewSet):
    serializer_class = WatchlistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Watchlist.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# ---------- Recommendation ViewSet ----------
class RecommendationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RecommendationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Recommendation.objects.filter(user=self.request.user).select_related("movie")
