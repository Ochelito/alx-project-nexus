from django.urls import path
from .views import TrendingList, tmdb_trending, MovieDetail, search, genres

urlpatterns = [
    path("trending_cached/", TrendingList.as_view(), name="trending_cached"),
    path("trending/", tmdb_trending, name="trending"),
    path("search/", search, name="search"),
    path("genres/", genres, name="genres"),
    path("<int:tmdb_id>/", MovieDetail.as_view(), name="movie_detail"),
]
