from rest_framework import generics, permissions
from .models import Review
from .serializers import ReviewSerializer
from rest_framework.views import APIView

class MovieReviewsList(generics.ListAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.AllowAny]

    def get(self, request, tmdb_id):
        reviews = Review.objects.filter(tmdb_id=tmdb_id)
        return Response([{"user": r.user.username, "rating": r.rating, "comment": r.comment} for r in reviews])

    def get_queryset(self):
        movie_id = self.kwargs["movie_tmdb_id"]
        return Review.objects.filter(movie__tmdb_id=movie_id).order_by("-created_at")

class CreateReview(generics.CreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def post(self, request):
        data = request.data
        review = Review.objects.create(
            user=request.user,
            tmdb_id=data["tmdb_id"],
            rating=data["rating"],
            comment=data["comment"]
        )
        return Response({"id": review.id})
