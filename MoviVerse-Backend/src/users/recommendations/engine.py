from users.models import User
from users.services import compute_recommendations_for_user, compute_recommendations_for_all_users

def generate_for_user(user: User, limit: int = 20):
    """
    Interface to generate recommendations for a single user.
    """
    compute_recommendations_for_user(user, limit)

def generate_for_all_users(limit: int = 20):
    """
    Interface to generate recommendations for all users.
    """
    compute_recommendations_for_all_users(limit)
