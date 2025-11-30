from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.admin.sites import AlreadyRegistered
from .models import Movie, Genre, Watchlist, MovieViewLog, TrendingMovie, MovieStats

User = get_user_model()

# Safe registration for User
try:
    admin.site.register(User)
except AlreadyRegistered:
    pass

# Register other models
admin.site.register(Movie)
admin.site.register(Genre)
admin.site.register(Watchlist)
admin.site.register(MovieViewLog)
admin.site.register(TrendingMovie)
admin.site.register(MovieStats)
