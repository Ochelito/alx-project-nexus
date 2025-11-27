from core.supabase_client import supabase

class Movie:
    table_name = "movies"

    @staticmethod
    def all():
        result = supabase.table(Movie.table_name).select("*").execute()
        return result.data

    @staticmethod
    def get(movie_id):
        result = supabase.table(Movie.table_name).select("*").eq("id", movie_id).execute()
        if result.data:
            return result.data[0]
        return None

    @staticmethod
    def create(title, description):
        result = supabase.table(Movie.table_name).insert({
            "title": title,
            "description": description
        }).execute()
        return result.data

class Recommendation:
    table_name = "recommendations"

    @staticmethod
    def all():
        result = supabase.table(Recommendation.table_name).select("*").execute()
        return result.data

    @staticmethod
    def create(movie_id, recommended_movie_id):
        result = supabase.table(Recommendation.table_name).insert({
            "movie_id": movie_id,
            "recommended_movie_id": recommended_movie_id
        }).execute()
        return result.data
