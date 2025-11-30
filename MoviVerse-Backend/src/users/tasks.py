from celery import shared_task
from users.models import User
from users.services import compute_recommendations_for_user, compute_recommendations_for_all_users

@shared_task
def generate_recommendations_for_user_task(user_id, limit=20):
    """
    Generate recommendations for a single user asynchronously.
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return f"User {user_id} does not exist."
    
    compute_recommendations_for_user(user, limit=limit)
    return f"Recommendations generated for {user.email}"


@shared_task
def generate_recommendations_for_all_users_task(limit=20):
    """
    Generate recommendations for all users asynchronously.
    """
    compute_recommendations_for_all_users(limit)
    return "Recommendations generated for all users."
