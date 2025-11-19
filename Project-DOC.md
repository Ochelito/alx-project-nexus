# alx-project-nexus

# MoviVerse – Full Project Documentation

## Overview
MoviVerse is a modern movie discovery and streaming-assistant platform built through collaboration between backend and frontend teams. The platform provides authenticated users access to movies, genres, reviews, watchlists, search functions, and personalized recommendations.

This documentation serves as a master reference for **backend developers**, **frontend collaborators**, and **project reviewers**.

---

# 1. Project Architecture

## 1.1 Tech Stack

### **Backend**
- Python 3.11  
- Django 5  
- Django REST Framework  
- PostgreSQL  
- Redis (Caching)  
- Celery (Async tasks)  
- Swagger & ReDoc (Documentation)  
- PyJWT / SimpleJWT (Auth)  
- CI/CD (GitHub Actions)

### **Frontend**
- React + Vite  
- TypeScript (optional)  
- TailwindCSS  
- Redux Toolkit / Zustand  
- Axios for API consumption  

---

# 2. Core Features

## 2.1 User Module
- User registration  
- Email verification (optional)  
- Login / Logout  
- JWT authentication  
- Profile management  
- Password reset & change  

### Backend Endpoint Examples
| Action | Method | Endpoint |
|--------|---------|----------|
| Register | POST | `/api/auth/register/` |
| Login | POST | `/api/auth/login/` |
| Profile | GET | `/api/auth/me/` |

---

## 2.2 Movies Module
Handles movie metadata.

### Features
- Fetch all movies  
- Get movie details  
- Search movies  
- Filter by genre, year, rating  

### Endpoints
| Action | Method | Endpoint |
|--------|--------|-----------|
| List all movies | GET | `/api/movies/` |
| Movie details | GET | `/api/movies/{id}/` |
| Search | GET | `/api/movies/search/?q=` |

---

## 2.3 Reviews Module
- Add a movie review  
- Edit a review  
- Delete a review  
- Public review list  

### Endpoints
| Action | Method | Endpoint |
|--------|--------|-----------|
| Create review | POST | `/api/reviews/` |
| Update review | PUT | `/api/reviews/{id}/` |
| Delete review | DELETE | `/api/reviews/{id}/` |
| List reviews | GET | `/api/reviews/movie/{movie_id}/` |

---

## 2.4 Watchlist Module
- Add movie to watchlist  
- Remove from watchlist  
- Retrieve user watchlist  

### Endpoints
| Action | Method | Endpoint |
|--------|--------|-----------|
| Add to watchlist | POST | `/api/watchlist/` |
| Remove | DELETE | `/api/watchlist/{id}/` |
| Get watchlist | GET | `/api/watchlist/` |

---

# 3. Backend Architecture Details

## 3.1 Folder Structure (Backend)

```
src/
 ├── config/
 │    ├── settings/
 │    ├── urls.py
 │    ├── wsgi.py
 │    └── asgi.py
 ├── apps/
 │    ├── users/
 │    ├── movies/
 │    ├── reviews/
 │    └── watchlist/
 ├── venv/
 └── manage.py
```

---

# 4. Frontend Architecture Overview

## 4.1 Component Structure

```
src/
 ├── components/
 ├── pages/
 ├── hooks/
 ├── store/
 ├── services/api.js
 └── App.jsx
```

---

## 4.2 API Consumption Standard

Frontend uses Axios:

```js
import axios from "axios";

export const api = axios.create({
  baseURL: "https://api.moviserver.com",
});
```

---

# 5. Database Schema

## 5.1 User Table
| Field | Type |
|--------|-------|
| id | UUID |
| email | string |
| password | hashed |
| is_verified | boolean |
| created_at | datetime |

## 5.2 Movie Table
| Field | Type |
|--------|-------|
| id | UUID |
| title | string |
| description | text |
| genre | FK Genre |
| rating | float |
| year | int |

## 5.3 Review Table
| Field | Type |
|--------|-------|
| id | UUID |
| user | FK User |
| movie | FK Movie |
| comment | text |
| stars | integer |

## 5.4 Watchlist Table
| Field | Type |
|--------|-------|
| id | UUID |
| user | FK User |
| movie | FK Movie |
| created_at | datetime |

---

# 6. Authentication (JWT)

### **Access Token** – short-lived  
### **Refresh Token** – long-lived  

Frontend stores:
- Access token → memory or secure storage  
- Refresh token → httpOnly cookie (recommended)

---

# 7. CI/CD

GitHub Actions workflow handles:
- linting  
- tests  
- migrations  
- deployment pipeline  

---

# 8. Collaboration Guidelines

## 8.1 Backend Responsibilities
- All API endpoints  
- Database design  
- Authentication  
- Documentation (Swagger)  
- Server deployment  
- Redis caching  
- CI/CD pipeline  

## 8.2 Frontend Responsibilities
- User interface  
- API consumption  
- State management  
- Routing  
- Validation  

---

# 9. Swagger Docs

Available at:

```
/api/docs/swagger/
/api/docs/redoc/
```

---

# 10. Running the Project Locally

### Backend

```bash
cd MoviVerse-Backend
source venv/scripts/activate
python manage.py runserver
```

### Frontend

```bash
cd moviverse-frontend
npm install
npm run dev
```

---

# 11. Future Features

- ML recommendation engine  
- Watch party  
- Notifications  
- Email verification  
- Social login (Google/Facebook)  

---

# 12. Contributors

| Name | Role |
|--------|--------|
| Idoko Augustine | Backend Lead |
| Faruq Abdul Azeez  | Frontend Developer |

---

# END OF DOCUMENT
