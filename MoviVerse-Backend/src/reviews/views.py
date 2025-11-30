from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Review
from .serializers import ReviewSerializer
from movies.models import Movie
from users.permissions import IsOwnerOrReadOnly
from .tasks import update_movie_rating


# ------------------------------------------------------------------------------
# List Reviews for a Movie
# ------------------------------------------------------------------------------
class MovieReviewsList(generics.ListAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        tmdb_id = self.kwargs.get("tmdb_id")
        return Review.objects.filter(
            movie__tmdb_id=tmdb_id
        ).select_related("user", "movie").order_by("-created_at")

    @swagger_auto_schema(
        tags=["Reviews"],
        operation_summary="List all reviews for a movie",
        operation_description="Returns all reviews associated with a movie using its TMDb ID.",
        manual_parameters=[
            openapi.Parameter(
                "tmdb_id",
                openapi.IN_PATH,
                description="TMDb ID of the movie",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={200: ReviewSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        data = [
            {
                "user": r.user.username,
                "rating": r.rating,
                "comment": r.comment,
                "created_at": r.created_at,
                "updated_at": r.updated_at
            }
            for r in queryset
        ]
        return Response(data)


# ------------------------------------------------------------------------------
# Full CRUD for a Single Review
# ------------------------------------------------------------------------------
class ReviewDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    lookup_field = "id"

    def get_queryset(self):
        return Review.objects.select_related("user", "movie")

    # --- Retrieve a review ---
    @swagger_auto_schema(
        tags=["Reviews"],
        operation_summary="Retrieve a single review",
        operation_description="Returns a single review by ID.",
        manual_parameters=[
            openapi.Parameter(
                "id",
                openapi.IN_PATH,
                description="Review ID",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={200: ReviewSerializer}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    # --- Update a review ---
    @swagger_auto_schema(
        tags=["Reviews"],
        operation_summary="Update your review",
        operation_description="Allows the authenticated owner to update their review.",
        request_body=ReviewSerializer,
        responses={200: ReviewSerializer}
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=["Reviews"],
        operation_summary="Partially update your review",
        request_body=ReviewSerializer,
        responses={200: ReviewSerializer}
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    # --- Delete a review ---
    @swagger_auto_schema(
        tags=["Reviews"],
        operation_summary="Delete your review",
        operation_description="Allows the authenticated owner to delete their review.",
        responses={204: "Review deleted successfully"}
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

    # Trigger rating recalculation
    def perform_update(self, serializer):
        review = serializer.save()
        update_movie_rating.delay(review.movie.tmdb_id)
        return review

    def perform_destroy(self, instance):
        movie_id = instance.movie.tmdb_id
        instance.delete()
        update_movie_rating.delay(movie_id)


# ------------------------------------------------------------------------------
# Optional: Function-based Create Review
# ------------------------------------------------------------------------------
@swagger_auto_schema(
    method="post",
    tags=["Reviews"],
    operation_summary="Create or update a review",
    operation_description="Creates a new review or updates an existing one by the same user for the same movie.",
    request_body=ReviewSerializer,
    responses={201: ReviewSerializer}
)
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def add_review(request):
    serializer = ReviewSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    review = serializer.save(user=request.user)

    update_movie_rating.delay(review.movie.tmdb_id)

    return Response({
        "id": review.id,
        "tmdb_id": review.movie.tmdb_id,
        "movie_title": review.movie.title,
        "rating": review.rating,
        "comment": review.comment,
        "created_at": review.created_at,
        "updated_at": review.updated_at
    }, status=status.HTTP_201_CREATED)


# ------------------------------------------------------------------------------
# Delete Review by TMDb ID
# ------------------------------------------------------------------------------
@swagger_auto_schema(
    method="delete",
    tags=["Reviews"],
    operation_summary="Delete a review for a movie",
    operation_description="Deletes the authenticated user's review for the given movie TMDb ID.",
    manual_parameters=[
        openapi.Parameter(
            "tmdb_id",
            openapi.IN_PATH,
            description="TMDb ID of the movie",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ],
    responses={200: "Review deleted successfully"}
)
@api_view(["DELETE"])
@permission_classes([permissions.IsAuthenticated])
def remove_review(request, tmdb_id):
    movie = get_object_or_404(Movie, tmdb_id=tmdb_id)
    review = Review.objects.filter(user=request.user, movie=movie).first()
    if not review:
        return Response({"detail": "Review not found."}, status=status.HTTP_404_NOT_FOUND)

    review.delete()
    update_movie_rating.delay(movie.tmdb_id)

    return Response({"detail": "Review deleted successfully."}, status=status.HTTP_200_OK)
