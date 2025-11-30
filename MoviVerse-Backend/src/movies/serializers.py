from rest_framework import serializers
from .models import Movie, Genre, Watchlist, MovieStats
from .services.tmdb_client import TMDbClient
from datetime import datetime

tmdb_client = TMDbClient()

# -----------------------------
# TMDb Movie Serializer (not DB-bound)
# -----------------------------
class TMDbMovieSerializer(serializers.Serializer):
    tmdb_id = serializers.IntegerField(source="id")
    title = serializers.CharField()
    description = serializers.CharField(source="overview", allow_blank=True, required=False)
    poster_url = serializers.SerializerMethodField()
    release_date = serializers.SerializerMethodField()
    vote_average = serializers.FloatField(required=False, default=0.0)
    vote_count = serializers.IntegerField(required=False, default=0)
    genre_ids = serializers.SerializerMethodField()
    genres = serializers.SerializerMethodField()  # Optional: return full genre names

    def get_poster_url(self, obj):
        path = obj.get("poster_path")
        return f"https://image.tmdb.org/t/p/w500{path}" if path else None

    def get_release_date(self, obj):
        # TMDb sometimes returns "" or None
        date_str = obj.get("release_date")
        if not date_str:
            return None
        try:
            # Convert to ISO format YYYY-MM-DD
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return None

    def get_genre_ids(self, obj):
        # TMDb detail endpoint: 'genres' list of dicts
        if obj.get("genres"):
            return [g["id"] for g in obj["genres"]]
        # TMDb list endpoints: sometimes 'genre_ids' is already a list
        return obj.get("genre_ids", [])

    def get_genres(self, obj):
        if obj.get("genres"):
            return [g.get("name") for g in obj["genres"] if g.get("name")]
        return []

# -----------------------------
# Local DB Serializers
# -----------------------------
class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ["tmdb_id", "name"]


class MovieSerializer(serializers.ModelSerializer):
    poster_url = serializers.SerializerMethodField()
    genre_names = serializers.SerializerMethodField()
    rating_summary = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = [
            "tmdb_id",
            "title",
            "description",
            "poster_url",
            "release_date",
            "release_year",
            "vote_average",
            "vote_count",
            "genres",
            "genre_names",
            "rating_summary",
        ]

    def get_poster_url(self, obj):
        return f"https://image.tmdb.org/t/p/w500{obj.poster_path}" if obj.poster_path else None

    def get_genre_names(self, obj):
        return [genre.name for genre in obj.genres.all()]

    def get_rating_summary(self, obj):
        return {"avg": obj.vote_average, "count": obj.vote_count}

    # -----------------------------
    # TMDb integration: fetch or create
    # -----------------------------
    @classmethod
    def fetch_or_create(cls, tmdb_id):
        """
        Fetch movie from DB; if missing or incomplete, pull from TMDb and create/update locally.
        """
        movie = Movie.objects.filter(tmdb_id=tmdb_id).first()
        created = False

        if movie is None:
            # Movie doesn't exist locally → fetch from TMDb
            data = tmdb_client.movie_detail(tmdb_id)
            movie = Movie.objects.create(
                tmdb_id=data["id"],
                title=data.get("title"),
                description=data.get("overview"),
                poster_path=data.get("poster_path"),
                release_date=data.get("release_date"),
                vote_average=data.get("vote_average", 0),
                vote_count=data.get("vote_count", 0),
                release_year=int(data.get("release_date", "0000")[:4]) if data.get("release_date") else None
            )
            created = True

        else:
            # Movie exists → update fields from TMDb
            data = tmdb_client.movie_detail(tmdb_id)
            movie.title = data.get("title")
            movie.description = data.get("overview")
            movie.poster_path = data.get("poster_path")
            movie.release_date = data.get("release_date")
            movie.vote_average = data.get("vote_average", 0)
            movie.vote_count = data.get("vote_count", 0)
            movie.release_year = int(movie.release_date[:4]) if movie.release_date else None
            movie.save()

        # Add/update genres
        for g in data.get("genres", []):
            genre_obj, _ = Genre.objects.get_or_create(
                tmdb_id=g["id"], defaults={"name": g["name"]}
            )
            movie.genres.add(genre_obj)

        # Ensure associated MovieStats exists
        MovieStats.objects.get_or_create(movie=movie)

        return movie, created

class WatchlistSerializer(serializers.ModelSerializer):
    movie = MovieSerializer(read_only=True)

    class Meta:
        model = Watchlist
        fields = ["user", "movie", "watched_at"]


class MovieStatsSerializer(serializers.ModelSerializer):
    movie = MovieSerializer(read_only=True)

    class Meta:
        model = MovieStats
        fields = [
            "movie",
            "avg_rating",
            "reviews_count",
            "favorites_count",
            "watch_count",
            "trending_score",
            "updated_at",
        ]
