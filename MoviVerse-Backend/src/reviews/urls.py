from django.urls import path
from .views import MovieReviewsList, CreateReview

urlpatterns = [
    path("movie/<int:movie_tmdb_id>/", MovieReviewsList.as_view(), name="movie_reviews"),
    path("create/", CreateReview.as_view(), name="create_review"),
]
