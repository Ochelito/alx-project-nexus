import requests
from django.conf import settings

BASE_URL = "https://api.themoviedb.org/3"

def tmdb_get(endpoint, params=None):
    if params is None:
        params = {}

    params["api_key"] = settings.TMDB_API_KEY

    url = f"{BASE_URL}/{endpoint}"

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
