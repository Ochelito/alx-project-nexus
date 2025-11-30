import time
import requests
from django.conf import settings
from requests.adapters import HTTPAdapter, Retry
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

TMDB_API_KEY = settings.TMDB_API_KEY
TMDB_BASE = "https://api.themoviedb.org/3"

class TMDbClient:
    def __init__(self, api_key=TMDB_API_KEY, session=None, rate_sleep=0.25, cache_timeout=600):
        if not api_key:
            raise RuntimeError("TMDB_API_KEY not set in environment")
        self.api_key = api_key
        self.session = session or requests.Session()
        self.rate_sleep = rate_sleep
        self.cache_timeout = cache_timeout

        retries = Retry(total=3, backoff_factor=1, status_forcelist=[502,503,504])
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

    def _get(self, path, params=None):
        params = params or {}
        params["api_key"] = self.api_key
        url = f"{TMDB_BASE}{path}"
        cache_key = f"tmdb:{path}?{'&'.join(f'{k}={v}' for k, v in sorted(params.items()))}"

        # Check cache first
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            resp = self.session.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            cache.set(cache_key, data, self.cache_timeout)
            time.sleep(self.rate_sleep)
            return data
        except requests.RequestException as e:
            logger.error(f"TMDb API request failed: {e}")
            return {"results": []}

    # -----------------------------
    # Convenience methods
    # -----------------------------
    def get_movie(self, tmdb_id):
        return self._get(f"/movie/{tmdb_id}", params={"append_to_response": "credits,keywords"})

    def movie_details(self, tmdb_id, append_to_response=None):
        params = {}
        if append_to_response:
            params["append_to_response"] = append_to_response
        return self._get(f"/movie/{tmdb_id}", params)

    def search_movies(self, query, page=1):
        return self._get("/search/movie", params={"query": query, "page": page})

    def genres(self):
        return self._get("/genre/movie/list")

    def popular(self, page=1):
        return self._get("/movie/popular", params={"page": page})

    def trending(self, media_type="movie", time_window="week"):
        return self._get(f"/trending/{media_type}/{time_window}")

    def get_trending(self):
        return self._get("/trending/movie/week").get("results", [])
