from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
User = settings.AUTH_USER_MODEL
