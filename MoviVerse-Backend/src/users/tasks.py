from celery import shared_task
from django.utils import timezone
from django.db.models import Q

from movies.models import Movie
from favorites.models import Favorite
from recommendations.models import Recommendation
from users.models import User

@shared_task
def generate_user_recommendations(user_id):
    """
    Generate movie recommendations for a user based on their favorite movies' genres.
    Avoid recommending movies the user has already favorited.
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return f"User with ID {user_id} does not exist."

    # Get all genres of the user's favorite movies
    favorite_movies = Movie.objects.filter(favorites__user=user)
    genres = set()
    for movie in favorite_movies:
        if movie.genre:
            # Split genres if multiple per movie (comma separated)
            genres.update([g.strip() for g in movie.genre.split(',')])

    if not genres:
        return f"No favorite genres found for user {user.username}."

    # Find recommended movies: same genres, not already favorited
    recommended_movies = Movie.objects.filter(
        Q(genre__iregex=r'(' + '|'.join(genres) + ')')  # matches any genre
    ).exclude(favorites__user=user)[:10]  # Limit to top 10 recommendations

    # Save recommendations
    for movie in recommended_movies:
        Recommendation.objects.update_or_create(
            user=user,
            movie=movie,
            defaults={
                'reason': 'Based on your favorite genres',
                'created_at': timezone.now()
            }
        )

    return f"{len(recommended_movies)} recommendations generated for user {user.username}."


@shared_task
def generate_all_recommendations():
    """
    Generate recommendations for all users.
    Can be scheduled to run periodically via Celery Beat.
    """
    users = User.objects.all()
    for user in users:
        generate_user_recommendations.delay(user.id)
    return f"Recommendation tasks scheduled for {users.count()} users."
