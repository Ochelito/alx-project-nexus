from django.contrib import admin
from .models import User, Recommendation
from django.contrib.admin.sites import AlreadyRegistered

try:
    admin.site.register(User)
except AlreadyRegistered:
    pass
admin.site.register(Recommendation)
