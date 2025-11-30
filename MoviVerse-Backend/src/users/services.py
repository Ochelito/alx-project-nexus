from movies.models import Movie
from users.models import User, Recommendation

def compute_recommendations_for_user(user: User, limit: int = 20):
    """
    Compute recommendations for a single user based on:
    - preferred_genres (list of TMDb genre IDs)
    - watch_history (list of TMDb movie IDs)
    Stores results in the Recommendation model.
    """
    preferred_genres = user.preferred_genres or []
    watched_tmdb_ids = set(user.watch_history or [])

    # --- Fallback if no preferences ---
    if not preferred_genres and not watched_tmdb_ids:
        fallback_movies = Movie.objects.order_by("-popularity")[:limit]
        Recommendation.objects.filter(user=user).delete()
        Recommendation.objects.bulk_create([
            Recommendation(
                user=user,
                movie_id=movie.tmdb_id,
                reason="Popular fallback",
                score=movie.popularity or 0
            )
            for movie in fallback_movies
        ])
        return

    # --- Candidate movies matching preferred genres ---
    candidates = Movie.objects.filter(
        genres__tmdb_id__in=preferred_genres
    ).distinct()

    scored = []

    for movie in candidates:
        if movie.tmdb_id in watched_tmdb_ids:
            continue  # Skip already watched movies

        score = 0

        # +2 points per matching genre
        movie_genres = set(movie.genres.values_list("tmdb_id", flat=True))
        common_genres = movie_genres.intersection(preferred_genres)
        score += len(common_genres) * 2.0

        # +0.1 * popularity as signal
        score += (movie.popularity or 0) * 0.1

        # Slight boost if not the last watched movie
        if watched_tmdb_ids:
            last_watched = list(watched_tmdb_ids)[-1]
            if movie.tmdb_id != last_watched:
                score += 0.2

        scored.append((score, movie))

    # Sort descending by score
    scored.sort(key=lambda x: x[0], reverse=True)

    # Clear old recommendations
    Recommendation.objects.filter(user=user).delete()

    # Save new recommendations
    Recommendation.objects.bulk_create([
        Recommendation(
            user=user,
            movie_id=movie.tmdb_id,
            reason="Genre & behavior match",
            score=score
        )
        for score, movie in scored[:limit]
    ])


def compute_recommendations_for_all_users(limit: int = 20):
    """
    Compute recommendations for all users.
    Can be scheduled via Celery Beat.
    """
    for user in User.objects.all():
        compute_recommendations_for_user(user, limit=limit)
