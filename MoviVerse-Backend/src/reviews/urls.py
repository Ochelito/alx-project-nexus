from django.urls import path
from .views import (
    MovieReviewsList,
    ReviewDetailAPIView,
    add_review,
    remove_review,
)

urlpatterns = [
    # List all reviews for a specific movie
    path("movie/<int:tmdb_id>/reviews/", MovieReviewsList.as_view(), name="movie-reviews-list"),
    
    # Retrieve, update, or delete a specific review by its ID
    path("review/<int:id>/", ReviewDetailAPIView.as_view(), name="review-detail"),
    
    # Create or update a review (function-based endpoint)
    path("review/add/", add_review, name="add-review"),
    
    # Delete a review by movie TMDb ID (function-based endpoint)
    path("review/remove/<int:tmdb_id>/", remove_review, name="remove-review"),
]
