from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Movie, Genre, Review, Favorite, Recommendation, Watchlist, MovieViewLog, TrendingMovie

User = get_user_model()

admin.site.register(User)
admin.site.register(Movie)
admin.site.register(Genre)
admin.site.register(Review)
admin.site.register(Favorite)
admin.site.register(Recommendation)
admin.site.register(Watchlist)
admin.site.register(MovieViewLog)
admin.site.register(TrendingMovie)
