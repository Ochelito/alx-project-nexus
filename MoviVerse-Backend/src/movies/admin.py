from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Movie, Genre, Watchlist, MovieViewLog, TrendingMovie, MovieStats

User = get_user_model()

admin.site.register(User)
admin.site.register(Movie)
admin.site.register(Genre)
admin.site.register(Watchlist)
admin.site.register(MovieViewLog)
admin.site.register(TrendingMovie)
admin.site.register(MovieStats)  # Add stats for admin visibility
