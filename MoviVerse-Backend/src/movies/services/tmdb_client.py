import requests
from django.conf import settings

class TMDbClient:
    BASE_URL = "https://api.themoviedb.org/3"

    def __init__(self, api_key=None):
        self.api_key = api_key or settings.TMDB_API_KEY

    def _get(self, endpoint, params=None):
        params = params or {}
        params["api_key"] = self.api_key
        resp = requests.get(f"{self.BASE_URL}{endpoint}", params=params)
        resp.raise_for_status()
        return resp.json().get("results", [])

    def trending(self, page=1):
        return self._get("/trending/movie/week", {"page": page})

    def search_movies(self, query, page=1):
        return self._get("/search/movie", {"query": query, "page": page})

    def movie_detail(self, tmdb_id):
        resp = requests.get(f"{self.BASE_URL}/movie/{tmdb_id}", params={"api_key": self.api_key})
        resp.raise_for_status()
        return resp.json()

    def genres(self):
        resp = requests.get(f"{self.BASE_URL}/genre/movie/list", params={"api_key": self.api_key})
        resp.raise_for_status()
        return resp.json().get("genres", [])
