from django.urls import path
from . import views

urlpatterns = [
    # -----------------------------
    # TMDb-based endpoints
    # -----------------------------
    path('movies/trending/', views.trending_movies, name='trending-movies'),
    path('movies/search/', views.search_movies, name='search-movies'),
    path('movies/<int:tmdb_id>/', views.movie_detail, name='movie-detail'),
    path('genres/', views.tmdb_genres, name='tmdb-genres'),

    # -----------------------------
    # Watchlist endpoints
    # -----------------------------
    path('watchlist/', views.WatchlistListView.as_view(), name='watchlist-list'),
    path('watchlist/add/', views.WatchlistCreateView.as_view(), name='watchlist-add'),

    # -----------------------------
    # Movie stats
    # -----------------------------
    path('movies/stats/', views.MovieStatsListView.as_view(), name='movie-stats-list'),
]
