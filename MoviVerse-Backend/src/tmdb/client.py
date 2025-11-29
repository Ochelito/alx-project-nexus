import time
import requests
from django.conf import settings
from requests.adapters import HTTPAdapter, Retry
from django.core.cache import cache

TMDB_API_KEY = settings.TMDB_API_KEY
TMDB_BASE = "https://api.themoviedb.org/3"

class TMDbClient:
    def __init__(self, api_key=TMDB_API_KEY, session=None, rate_sleep=0.25):
        if not api_key:
            raise RuntimeError("TMDB_API_KEY not set in environment")
        self.api_key = api_key
        self.session = session or requests.Session()
        self.rate_sleep = rate_sleep
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[502,503,504])
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

    def _get(self, path, params=None):
        params = params or {}
        params["api_key"] = self.api_key
        url = f"{self.TMBD_BASE}{path}"
        cache_key = f"tmdb_{path}_{str(params)}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        resp = requests.get(url, params=params)
        if resp.status_code != 200:
            return {"results": []}
        data = resp.json()
        cache.set(cache_key, data, 600)  # cache 10 minutes
        return data
        resp = self.session.get(f"{TMDB_BASE}{path}", params=params, timeout=15)
        resp.raise_for_status()
        time.sleep(self.rate_sleep)  # polite rate limiting
        return resp.json()

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
        return self._get("/trending/movie/week")["results"] 
