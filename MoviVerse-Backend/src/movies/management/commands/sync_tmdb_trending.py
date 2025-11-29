from django.core.management.base import BaseCommand
from tmdb.client import TMDbClient
from movies.models import Movie, Genre
from django.utils.dateparse import parse_date

class Command(BaseCommand):
    help = "Sync TMDb trending movies into local DB"

    def handle(self, *args, **options):
        client = TMDbClient()
        data = client.trending(page=1)
        results = data.get("results", [])
        for item in results:
            tmdb_id = item["id"]
            movie, created = Movie.objects.update_or_create(
                tmdb_id=tmdb_id,
                defaults={
                    "title": item.get("title") or item.get("name") or "",
                    "overview": item.get("overview", ""),
                    "poster_path": item.get("poster_path"),
                    "popularity": item.get("popularity", 0.0),
                    "vote_average": item.get("vote_average", 0.0),
                    "vote_count": item.get("vote_count", 0),
                }
            )
            # genres
            for g in item.get("genre_ids", []):
                genre, _ = Genre.objects.get_or_create(tmdb_id=g, defaults={"name": str(g)})
                movie.genres.add(genre)
            movie.save()
        self.stdout.write(self.style.SUCCESS("Synced trending"))
