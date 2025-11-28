from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MovieViewSet, GenreViewSet, ReviewViewSet,
    WatchlistViewSet, RecommendationViewSet
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import  # noqa: rearranged imports
    # (we use a small auth register view below; add it into views.py or create separate file)

router = DefaultRouter()
router.register(r"movies", MovieViewSet, basename="movies")
router.register(r"genres", GenreViewSet, basename="genres")
router.register(r"reviews", ReviewViewSet, basename="reviews")
router.register(r"watchlist", WatchlistViewSet, basename="watchlist")
router.register(r"recommendations", RecommendationViewSet, basename="recommendations")

# Add register endpoint below (we'll create it in a small auth view)
from .views import RegisterView

urlpatterns = [
    path("", include(router.urls)),
    path("auth/register/", RegisterView.as_view(), name="auth_register"),
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
