# devboard-auth

Authentication microservice for the Devboard platform. Handles user registration, login, JWT access/refresh tokens, email verification, and session management.

## Stack

- **FastAPI** — web framework
- **SQLAlchemy** (async) — ORM
- **PostgreSQL** — database
- **Alembic** — migrations
- **python-jose** — JWT
- **bcrypt** — password hashing
- **httpx** — communicates with devboard-email

## Environment Variables

Copy `.env.example` to `.env` and fill in the values.

| Variable | Description |
|---|---|
| `DATABASE_URL` | Async PostgreSQL URL (`postgresql+asyncpg://...`) |
| `DATABASE_URL_SYNC` | Sync PostgreSQL URL (`postgresql+psycopg2://...`) |
| `POSTGRES_PASSWORD` | PostgreSQL password — used by Docker Compose to configure the DB container |
| `JWT_SECRET` | Secret key for signing JWTs |
| `FRONTEND_URL` | Base URL of the frontend (used in verification email links) |
| `EMAIL_SERVICE_URL` | URL of the devboard-email service |
| `EMAIL_SERVICE_SECRET_KEY` | Shared secret key for calling devboard-email |

## Running with Docker

```bash
# Build the image
docker compose up --build -d

# Run migrations
docker compose exec devboard-auth alembic upgrade head

# Stop containers
docker compose down
```

## API

Base path: `/auth`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/auth/register` | — | Register a new user |
| `POST` | `/auth/login` | — | Login and receive access + refresh tokens |
| `POST` | `/auth/refresh-token` | — | Exchange refresh token for new tokens |
| `POST` | `/auth/logout` | — | Revoke a refresh token |
| `POST` | `/auth/logout-all` | Bearer | Revoke all refresh tokens for the current user |
| `GET` | `/auth/verify-email` | — | Verify email via token from email link |
| `POST` | `/auth/resend-verification` | — | Resend verification email |
| `GET` | `/health` | — | Health check |
| `GET` | `/health/db` | — | Database connectivity check |

## Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```
