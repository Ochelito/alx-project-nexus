from django.urls import path
from . import views

urlpatterns = [
    # URL pattern for trending movies
    path("trending/", views.TrendingMoviesView.as_view(), name="trending-movies"),
]
