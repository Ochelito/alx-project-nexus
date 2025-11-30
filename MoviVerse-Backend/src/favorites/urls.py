from django.urls import path
from .views import (
    FavoriteListView,
    AddFavoriteAPIView,
    RemoveFavoriteAPIView,
    list_favorites
)

urlpatterns = [
    # List all favorites for the authenticated user
    path("", FavoriteListView.as_view(), name="favorites-list"),

    # Add a movie to favorites
    path("add/", AddFavoriteAPIView.as_view(), name="favorites-add"),

    # Remove a movie from favorites
    path("remove/", RemoveFavoriteAPIView.as_view(), name="favorites-remove"),

    # Optional formatted list of favorites
    path("formatted/", list_favorites, name="favorites-formatted"),
]
