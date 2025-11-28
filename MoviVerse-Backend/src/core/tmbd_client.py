import os
import time
import requests

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE = "https://api.themoviedb.org/3"

class TMDbClient:
    def __init__(self, api_key=TMDB_API_KEY, session=None, rate_sleep=0.25):
        if not api_key:
            raise RuntimeError("TMDB_API_KEY not set in environment")
        self.api_key = api_key
        self.session = session or requests.Session()
        self.rate_sleep = rate_sleep

    def _get(self, path, params=None):
        params = params or {}
        params["api_key"] = self.api_key
        resp = self.session.get(f"{TMDB_BASE}{path}", params=params, timeout=15)
        resp.raise_for_status()
        time.sleep(self.rate_sleep)  # polite rate limiting
        return resp.json()

    def get_movie(self, tmdb_id):
        return self._get(f"/movie/{tmdb_id}", params={"append_to_response": "credits,keywords"})

    def search_movies(self, query, page=1):
        return self._get("/search/movie", params={"query": query, "page": page})

    def popular(self, page=1):
        return self._get("/movie/popular", params={"page": page})

    def trending(self, media_type="movie", time_window="week"):
        return self._get(f"/trending/{media_type}/{time_window}")
        