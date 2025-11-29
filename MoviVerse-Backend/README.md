# MovieBox — Django Backend (TMDb Integrated)

A production-ready Django REST backend for a movie app integrated with The Movie Database (TMDb). This repository provides modular apps for `users`, `movies`, `reviews`, and `favorites`, a TMDb service layer, JWT authentication, caching (Redis), Celery background tasks, and CI configuration. The project is designed to be consumed by a frontend (React + Vite).

---

## Table of contents

1. [Features](#features)
2. [Quick start (local development)](#quick-start-local-development)
3. [Environment variables](#environment-variables)
4. [Project layout](#project-layout)
5. [Run the app (commands)](#run-the-app-commands)
6. [TMDb integration & syncing](#tmdb-integration--syncing)
7. [Background tasks (Celery)](#background-tasks-celery)
8. [Caching strategy](#caching-strategy)
9. [API overview (important endpoints)](#api-overview-important-endpoints)
10. [Testing & CI](#testing--ci)
11. [Deployment (production)](#deployment-production)
12. [Security & best practices](#security--best-practices)
13. [Troubleshooting](#troubleshooting)
14. [Next steps & roadmap](#next-steps--roadmap)
15. [License](#license)

---

## Features

- Modular Django apps: `users`, `movies`, `reviews`, `favorites`, `tmdb` service layer.
- JWT authentication with `djangorestframework-simplejwt`.
- TMDb client with retries and resilient requests.
- Trending and search endpoints (TMDb-backed) and a local trending-sync command.
- Hybrid recommendations (genre-based + TMDb fallback).
- Redis caching for expensive TMDb endpoints.
- Celery tasks for scheduled syncs (requires Redis broker).
- DRF pagination, Swagger docs via `drf-yasg`.
- GitHub Actions CI template for tests.

---

## Quick start (local development)

1. Clone the repository:

```bash
git clone <your-repo-url>
cd moviebox
```

2. Create virtual environment & install dependencies:

```bash
python -m venv venv
source venv/bin/activate   # macOS / Linux
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

3. Copy and fill the `.env` file (see [Environment variables](#environment-variables)):

```bash
cp .env.example .env
# Edit .env and set values (POSTGRES, TMDB_API_KEY, SECRET_KEY, etc.)
```

4. Run migrations and create a superuser:

```bash
python manage.py migrate
python manage.py createsuperuser
```

5. Run the development server:

```bash
python manage.py runserver
```

6. (Optional) Sync trending movies once:

```bash
python manage.py sync_tmdb_trending
```

---

## Environment variables

Use the `.env` file (do NOT commit secrets). The `.env.example` file lists all variables; key ones below:

- `DJANGO_SECRET_KEY` — Django secret key.
- `DJANGO_DEBUG` — `True` for local dev, `False` for production.
- `DJANGO_ALLOWED_HOSTS` — comma-separated hosts.
- `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_HOST` / `POSTGRES_PORT`
- `REDIS_URL` — e.g. `redis://localhost:6379/0` (used for cache & Celery broker/result backend).
- `TMDB_API_KEY` — Your TMDb API key. (Get one at https://www.themoviedb.org/)
- `SIMPLE_JWT_ACCESS_TOKEN_LIFETIME_MINUTES` — JWT lifetime.

Make sure **`.env`** is listed in `.gitignore`.

---

## Project layout (important files)

```
moviebox/
├── moviebox/          # Django project settings + celery
├── users/             # auth, profiles, recommendations
├── movies/            # movie model, trending, sync command
├── reviews/           # user reviews
├── favorites/         # user favorites
├── tmdb/              # TMDb client/service
├── requirements.txt
├── .env.example
└── .github/workflows/ci.yml
```

---

## Run the app (commands)

- Run server:
  ```bash
  python manage.py runserver
  ```

- Run migrations:
  ```bash
  python manage.py migrate
  ```

- Create superuser:
  ```bash
  python manage.py createsuperuser
  ```

- Sync TMDb trending (one-off or via Celery beat):
  ```bash
  python manage.py sync_tmdb_trending
  ```

- Start Celery worker (requires Redis running):
  ```bash
  celery -A moviebox worker --loglevel=info
  ```

- Run tests:
  ```bash
  python manage.py test
  ```

---

## TMDb integration & syncing

- Store your `TMDB_API_KEY` in `.env`.
- The `tmdb.client.TMDbClient` centralizes TMDb requests and applies retry logic.
- For periodic syncing of trending movies into the local DB, use the management command:

```bash
python manage.py sync_tmdb_trending
```

- Consider scheduling `sync_tmdb_trending` nightly via Celery Beat or a cron job.

---

## Background tasks (Celery)

- `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` point to the same Redis instance by default (set `REDIS_URL`).

- Example to start worker:

```bash
celery -A moviebox worker --loglevel=info
```

- If you add periodic tasks, set up Celery Beat or an external scheduler. Example (production recommended): run a Beat process or use a scheduler service.

---

## Caching strategy

- Redis is used to cache TMDb responses (trending, genres, etc.) for short durations to reduce API calls and improve response speed.
- Cache keys used by default (examples): `tmdb_trending`, `tmdb_genres`.
- Tune TTLs depending on how fresh you want data to be (e.g., trending -> 10 minutes, genres -> 24 hours).

---

## API overview (important endpoints)

> Base path: `/api/`

### Users
- `POST /api/users/register/` — register
- `POST /api/users/login/` — obtain JWT tokens (`access`, `refresh`)
- `POST /api/users/token/refresh/` — refresh token
- `GET|PUT /api/users/me/` — get or update profile
- `GET /api/users/recommendations/` — hybrid recommendations (genre-based, fallback to TMDb trending)

### Movies
- `GET /api/movies/trending/` — TMDb trending (cached)
- `GET /api/movies/trending_cached/` — local DB trending (synced)
- `GET /api/movies/search/?q=...` — search TMDb
- `GET /api/movies/genres/` — list TMDb genres (cached)
- `GET /api/movies/<tmdb_id>/` — local movie detail (if synced)

### Reviews
- `GET /api/reviews/movie/<movie_tmdb_id>/` — list reviews for a movie
- `POST /api/reviews/create/` — create review (auth required)

### Favorites
- `GET /api/favorites/` — list user favorites (auth required)
- `POST /api/favorites/add/` — add favorite by `tmdb_id`
- `POST /api/favorites/remove/` — remove favorite by `tmdb_id`

---

## Testing & CI

- A basic GitHub Actions workflow is included at `.github/workflows/ci.yml`. It sets up Postgres service and runs tests.
- Add more CI steps: linting (Black/flake8), security checks, DB migrations check, and integration tests that mock TMDb.

---

## Deployment (production)

### Recommended stack
- PostgreSQL (managed, e.g., RDS, ElephantSQL)
- Redis (managed or hosted)
- Gunicorn as WSGI server
- Nginx as reverse proxy
- Celery workers (and optionally Celery Beat) for background tasks
- Optional: Docker or direct systemd services

### Checklist for production
1. `DJANGO_DEBUG=False`
2. Secure `DJANGO_SECRET_KEY` stored in environment
3. Configure `ALLOWED_HOSTS` properly
4. Use HTTPS (Let’s Encrypt or vendor TLS)
5. Set up staticfiles (collectstatic) behind a CDN or via whitenoise + nginx
6. Configure process manager (systemd / supervisor / gunicorn + nginx)
7. Monitor logs (Sentry or similar) and set alerts
8. Rate-limit endpoints (DRF throttling) if public

### Example Gunicorn systemd service
```
[Unit]
Description=Gunicorn instance to serve moviebox
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/moviebox
ExecStart=/path/to/venv/bin/gunicorn moviebox.wsgi:application --bind 0.0.0.0:8000

[Install]
WantedBy=multi-user.target
```

---

## Security & best practices

- Never commit `.env` or secret keys.
- Use HTTPS and HSTS headers.
- Set `SECURE_BROWSER_XSS_FILTER`, `X_FRAME_OPTIONS`, and other common hardening settings.
- Keep dependencies up-to-date and run `pip-audit` occasionally.
- Use database role with least privilege for the app.

---

## Troubleshooting

- `OperationalError: could not connect to server` — check Postgres host/port, and that DB is running.
- `TMDb API 401` — check `TMDB_API_KEY` and that it’s correctly set in the environment.
- `Celery cannot connect to broker` — ensure `REDIS_URL` is correct and Redis is running.
- `AUTH_USER_MODEL` changed after migrations` — if you change `AUTH_USER_MODEL`, you must recreate DB or follow Django docs for migrations.

---

## Next steps & roadmap

- Add more robust recommendation engine (collaborative filtering or matrix-factorization).
- Add request throttling & API rate limits.
- Add image proxying for TMDb posters, optionally resize images.
- Add more thorough unit, integration and end-to-end tests (including mocking TMDb API).
- Add Docker + docker-compose for local reproducible dev environment (not included here at user's request).

---


