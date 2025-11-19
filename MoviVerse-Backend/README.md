# MoviVerse — Backend Documentation

## 1. Project Summary (one-liner)
**MoviVerse backend**: A production-ready Django REST backend providing movie discovery, trending, personalized recommendations, user auth & preferences, TMDb integration, Redis caching, background processing, and Swagger documentation.

---

## 2. Tech Stack (backend-only)
- Python 3.10+
- Django 4.2+ (or latest LTS)
- Django REST Framework (DRF)
- PostgreSQL (primary relational DB)
- Redis (caching + Celery broker option)
- Celery + Celery Beat (background jobs)
- drf-spectacular or drf-yasg (Swagger/OpenAPI)
- requests / httpx (external HTTP to TMDb)
- djangorestframework-simplejwt (JWT auth)
- pytest + pytest-django (testing)
- black, isort, flake8 (format & lint)
- GitHub Actions (CI/CD)
- Hosting: Render / Railway / Heroku (no Docker local requirement)

---

## 3. Goals & Non-Functional Requirements
- Correctness: endpoints must return well-formed JSON and proper HTTP status codes.
- Performance: trending & recommendations must use Redis caching; target <300ms median for cached endpoints.
- Security: JWT auth, CORS, input validation, HTTPS in production.
- Observability: logging, health check, and basic metrics.
- Maintainability: modular apps, clear documentation, and tests (unit + integration).
- Deployability without Docker: use hosting that accepts Python deployments (Render/Railway/Heroku).

---

## 4. Environment Variables (minimum)
- SECRET_KEY
- DEBUG (True/False)
- ALLOWED_HOSTS
- DATABASE_NAME / DATABASE_USER / DATABASE_PASSWORD / DATABASE_HOST / DATABASE_PORT (or DATABASE_URL)
- REDIS_URL (e.g., redis://:password@host:port/0)
- TMDB_API_KEY
- EMAIL_BACKEND config (for password reset)
- SENTRY_DSN (optional)
- SIMPLE_JWT settings (token lifetimes) as env vars

---

## 5. Data Models (concise surface-level schema)
All PKs are UUIDs unless noted.

### User (custom `AbstractUser`)
- id, email (unique), username, password (hashed), is_staff, is_active, date_joined
- profile fields: avatar_url, locale, bio (separate Profile model optional)

### Genre
- id, name, slug

### Person (actor/director)
- id, name, tmdb_id (optional), bio, dob, photo_url

### Movie
- id, tmdb_id (int), title, overview, release_date, runtime, poster_url, backdrop_url, vote_average, language
- relations: genres (M2M), cast (M2M through MovieCast), crew (M2M through MovieCrew)
- metadata fields: popularity_score (cached/denormalized)

### MovieCast / MovieCrew
- movie (FK), person (FK), role, character_name

### FavoriteMovie
- id, user (FK), movie_tmdb_id (int), title, poster_url, added_at

### Review / Rating
- id, user (FK), movie_tmdb_id, rating (1-5), text, created_at, updated_at

### WatchHistory
- id, user (FK), movie_tmdb_id, watched_at, progress_seconds (optional)

### TrendingCache / RecommendationCache (optional models)
- key, payload (JSON), ttl, last_updated

---

## 6. Key Endpoints (full list, method, path, purpose)

### Auth & Users
- `POST /api/auth/register/` — register user. Body: {email, username, password}
- `POST /api/auth/login/` — obtain JWT. Body: {email, password} → returns access & refresh tokens
- `POST /api/auth/token/refresh/` — refresh access token
- `POST /api/auth/logout/` — optional: blacklist refresh token
- `GET /api/auth/me/` — get current user profile (Auth required)
- `POST /api/auth/password-reset/` — request reset (email)
- `POST /api/auth/password-reset/confirm/` — confirm reset

### Movies (TMDb backed)
- `GET /api/movies/trending/?time_range=day|week&limit=20` — trending movies (cached)
- `GET /api/movies/popular/?page=1` — popular movies (TMDb)
- `GET /api/movies/top-rated/?page=1` — top rated
- `GET /api/movies/upcoming/` — upcoming releases
- `GET /api/movies/{tmdb_id}/` — movie detail (aggregates TMDb endpoints: details, credits, videos)
- `GET /api/movies/{tmdb_id}/similar/` — movies similar to this (TMDb similar + local)
- `GET /api/movies/search/?q=&genre=&year=&page=` — search & filter (supports PostgreSQL FTS if enabled)

### Preferences & Interactions
- `POST /api/user/favorites/` — add to favorites. Body: {tmdb_id, title, poster_url}
- `GET /api/user/favorites/` — list user's favorites (Auth required)
- `DELETE /api/user/favorites/{id}/` — remove favorite
- `POST /api/user/watchlist/` — add to watchlist
- `GET /api/user/watchlist/` — list watchlist
- `POST /api/movies/{tmdb_id}/track-view/` — record view event (user or anonymous)
- `GET /api/user/history/` — view watch history (Auth required)

### Reviews & Ratings
- `POST /api/movies/{tmdb_id}/reviews/` — create review (Auth required)
- `GET /api/movies/{tmdb_id}/reviews/` — list reviews
- `PUT /api/reviews/{id}/` — update review (owner only)
- `DELETE /api/reviews/{id}/` — delete review (owner or admin)

### Recommendations & Trending (personalized)
- `GET /api/movies/recommendations/` — personalized recommendations (Auth required)
  - Query params: `limit`, `strategy=hybrid|content|collab`
- `GET /api/movies/{tmdb_id}/recommendations/` — item-based recommendations

### Admin (protected, admin-only)
- CRUD endpoints for Movie metadata (if persisting)
- Endpoints to trigger cache refresh, re-sync TMDb data, and view analytics
- `GET /api/admin/analytics/` — basic metrics JSON

### Docs & Health
- `GET /api/docs/` — Swagger UI (drf-spectacular or drf-yasg)
- `GET /health/` — liveness & readiness checks

---

## 7. TMDb Integration (detailed)

### 7.1 API Key
- Store TMDb API key in `TMDB_API_KEY` env var. Never expose to frontend.

### 7.2 Required TMDb endpoints used
- `/trending/movie/day` and `/trending/movie/week`
- `/movie/popular`, `/movie/top_rated`, `/movie/upcoming`
- `/movie/{id}`, `/movie/{id}/credits`, `/movie/{id}/videos`, `/movie/{id}/similar`
- `/search/multi` for search autocomplete
- `/configuration` for image base URLs

### 7.3 Orchestration Layer
- Implement `services/tmdb.py` that wraps HTTP calls and normalizes TMDb responses to the internal schema.
- Validate responses and return consistent JSON structure for frontend consumption.

### 7.4 Caching policy for TMDb calls
- Trending/popular/top-rated: cache in Redis with TTL = 10 minutes (configurable)
- Movie detail pages: cache for 12–24 hours; invalidate on admin update
- Search results: short TTL (e.g., 60 seconds) + rate limiting
- Use cache keys like `tmdb:trending:week`, `tmdb:movie:{id}:detail`

### 7.5 Rate-limiting & Retry
- Implement request retries with exponential backoff for transient errors
- Circuit breaker: if TMDb fails repeatedly, fall back to cached DB content or return graceful error
- Log TMDb call failures and alerts

---

## 8. Caching & Performance

### Redis usage
- Caches for trending, popular, movie details, search suggestions
- Optional: use Redis as Celery broker & result backend
- Use Django `cache` framework with RedisCache backend
- Use `select_related` and `prefetch_related` in heavy queries
- Add DB indexes on frequently filtered fields: `tmdb_id`, `release_date`, `vote_average`, `title` (GIN index for FTS)

### Pagination & Rate Limiting
- Use page-based pagination for list endpoints (DRF `PageNumberPagination`)
- Implement global rate-limiting (per-IP & per-user) for endpoints hitting TMDb to protect API key

---

## 9. Recommendation Engine (design & endpoints)

### Strategy: Hybrid (Content-based + Collaborative)
- **Content-based**: compute item vectors from genres, tags, cast, director, keywords. Use cosine similarity (offline precomputation).
- **Collaborative**: use user-item interaction matrix (ratings, favorites, watch history). Implement simple nearest-neighbors or matrix factorization offline using periodic jobs.
- **Hybrid**: combine scores with weights (e.g., 0.6 content + 0.4 collaborative).

### Implementation notes
- Precompute recommendations for active users periodically (Celery scheduled job) and cache results in Redis or store in `RecommendationCache` model.
- Expose `/api/movies/recommendations/` to return cached personalized lists; fallback to content-based if collaborative data is sparse.

---

## 10. Trending Engine (detailed)

### Inputs
- View counts (track via `/track-view/`)
- Unique viewers count
- Ratings (recent rating averages)
- Recency (recentness boost)

### Process
- Aggregation job (daily via Celery Beat) that computes trending scores and persists top-N in `TrendingCache` and Redis.
- Endpoint `/api/movies/trending/` reads from Redis for low-latency responses.

---

## 11. Background Jobs (Celery tasks)

### Required tasks
- `tasks.generate_daily_trending()` — compute trending using recent metrics
- `tasks.generate_recommendations()` — compute per-user recommendations periodically
- `tasks.sync_tmdb_movie(id)` — fetch & update movie details from TMDb
- `tasks.send_email()` — for notifications and password reset
- `tasks.cleanup_media()` — delete orphan files

### Infrastructure
- Use Redis or RabbitMQ as broker (Redis recommended for simplicity)
- Celery Beat for schedule

---

## 12. Admin & Analytics

### Admin features (API + Django Admin)
- CRUD for movies/genres/tags
- Trigger manual TMDb sync for specific movies
- View logs & failed tasks
- Export analytics metrics (CSV/JSON)

### Analytics endpoints (examples)
- `/api/admin/analytics/most-watched/`
- `/api/admin/analytics/new-users/`
- `/api/admin/analytics/dau/`

---

## 13. Testing Strategy

### Unit tests
- Models, serializers, utility functions, permission classes

### Integration tests
- API endpoints using DRF APIClient
- Mock TMDb responses using `responses` or `requests-mock`

### End-to-end tests (optional)
- Use a staging DB & controlled TMDb key or mocked TMDb proxy

### Coverage
- Aim for 70%+ coverage for backend codebase; critical paths near 90%

---

## 14. Security Best Practices

- Use HTTPS in production
- Keep DEBUG=False in production
- Strong SECRET_KEY via env var
- CORS restricted to frontend origins
- Rate limit endpoints (esp. search & TMDb proxied endpoints)
- Input validation in serializers
- Avoid exposing TMDb API key; server-side calls only

---

## 15. CI/CD (GitHub Actions) — Required workflow

### On PR
- Run linters (black, isort, flake8)
- Run tests (unit + integration)
- Static analysis (optional mypy)
- Security checks (bandit optional)

### On merge to main
- Run migrations on deploy target
- Run migration tests
- Deploy to host (Render/Railway/Heroku) using GitHub Secrets for env vars
- Run health check endpoint

**Note:** Since Docker is not allowed locally, rely on host platform's Python buildpacks / deploy method.

---

## 16. Monitoring & Observability

- Structured logs (JSON recommended)
- Health endpoints (`/health/`)
- Error tracking (Sentry integration optional)
- Metrics: request durations, error rates, cache hit ratio

---

## 17. Deliverables (what you must hand in)

- GitHub repo with clear commit history and meaningful commits
- `README.md` with setup instructions, env vars, and run commands
- Swagger UI accessible at `/api/docs/` (or generate `openapi.json`/yaml)
- Managed Postgres & Redis connection instructions (or dev instructions)
- CI workflow file `.github/workflows/ci.yml`
- Tests & coverage report
- Short demo script (curl examples) showing auth, trending, recommendations, add favorite
- Deployed URL(s) with Swagger docs (if possible)

---

## 18. Milestones (suggested)

**MVP (week 1–2)**
- Auth (JWT), basic user model
- TMDb wrapper service, trending endpoint (cached)
- Favorites model & endpoints
- Swagger basic docs

**Phase 2 (week 3)**
- Movie detail pages (TMDb aggregation)
- Watchlist, reviews & ratings
- Recommendations basic (content-based)

**Phase 3 (week 4)**
- Collaborative recommendations, background jobs, Celery + Redis
- Admin endpoints & analytics
- CI/CD & deployment

---

## 19. Appendix — Example Redis Key Naming
- `tmdb:trending:week`
- `tmdb:movie:{id}:detail`
- `user:{user_id}:recommendations`
- `movie:{tmdb_id}:views:daily`

---

## 20. Notes & Pitfalls to avoid
- Don’t expose TMDb API key to client
- Normalize TMDb data to your schema (do not pass raw)
- Cache aggressively but invalidate on content changes
- Use database transactions for critical updates (reviews, ratings)
- Mock external APIs during tests to avoid rate limits

---

# End of Document — MoviVerse Backend Requirements (REST + Swagger)