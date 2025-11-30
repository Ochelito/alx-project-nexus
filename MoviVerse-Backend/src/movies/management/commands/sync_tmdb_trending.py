from django.core.management.base import BaseCommand
from movies.services.tmdb_client import TMDbClient
from movies.models import Movie, Genre, MovieStats, TrendingMovie
from django.utils import timezone

class Command(BaseCommand):
    help = "Sync TMDb trending movies into local DB and create related stats"

    def handle(self, *args, **options):
        client = TMDbClient()
        self.stdout.write("Fetching trending movies from TMDb...")
        try:
            data = client.trending(page=1)
        except Exception as e:
            self.stderr.write(f"Failed to fetch trending movies: {e}")
            return

        results = data.get("results", [])
        for rank, item in enumerate(results, start=1):
            tmdb_id = item["id"]

            # Fetch or create movie
            movie, created = Movie.objects.update_or_create(
                tmdb_id=tmdb_id,
                defaults={
                    "title": item.get("title") or item.get("name") or "",
                    "description": item.get("overview", ""),
                    "poster_path": item.get("poster_path"),
                    "popularity": item.get("popularity", 0.0),
                    "vote_average": item.get("vote_average", 0.0),
                    "vote_count": item.get("vote_count", 0),
                    "release_year": None,  # Could parse from release_date if needed
                }
            )

            # Ensure genres exist and link to movie
            for genre_id in item.get("genre_ids", []):
                genre, _ = Genre.objects.get_or_create(
                    tmdb_id=genre_id,
                    defaults={"name": str(genre_id)}  # Ideally replace with actual TMDb genre name
                )
                movie.genres.add(genre)

            # Ensure MovieStats exists
            MovieStats.objects.get_or_create(movie=movie)

            # Add to TrendingMovie table
            TrendingMovie.objects.update_or_create(
                movie=movie,
                fetched_at=timezone.now(),
                defaults={"rank": rank, "score": item.get("popularity", 0.0)}
            )

            movie.save()

        self.stdout.write(self.style.SUCCESS(f"Successfully synced {len(results)} trending movies."))
