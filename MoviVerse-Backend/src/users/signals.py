from django.conf import settings
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.apps import apps

from users.tasks import generate_recommendations_for_user

User = apps.get_model(settings.AUTH_USER_MODEL)


@receiver(post_save, sender=User)
def create_user_recommendations(sender, instance, created, **kwargs):
    """
    Trigger recommendation generation for a new user.
    """
    if created:
        generate_recommendations_for_user.delay(instance.id)


@receiver(pre_save, sender=User)
def update_user_recommendations(sender, instance, **kwargs):
    """
    Trigger recommendation generation when preferred_genres or watch_history changes.
    """
    if not instance.pk:
        # Skip if user is being created (handled in post_save)
        return

    try:
        old_instance = User.objects.get(pk=instance.pk)
    except User.DoesNotExist:
        return

    if old_instance.preferred_genres != instance.preferred_genres or \
       old_instance.watch_history != instance.watch_history:
        generate_recommendations_for_user.delay(instance.id)
