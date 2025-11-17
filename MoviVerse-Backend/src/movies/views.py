from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .tmdb import tmdb_get


class TrendingMoviesView(APIView):
    """
    Returns trending movies from TMDb.
    """

    def get(self, request):
        data = tmdb_get("trending/movie/week")

        if "error" in data:
            return Response(
                {"detail": "Failed to fetch trending movies", "error": data["error"]},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(data, status=status.HTTP_200_OK)
