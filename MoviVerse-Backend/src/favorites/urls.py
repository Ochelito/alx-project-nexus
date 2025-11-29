from django.urls import path
from .views import FavoritesList, add_favorite, remove_favorite

urlpatterns = [
    path("", FavoritesList.as_view(), name="favorites_list"),
    path("add/", add_favorite, name="favorites_add"),
    path("remove/", remove_favorite, name="favorites_remove"),
]
