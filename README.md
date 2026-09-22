# devboard-auth

**Who are you?** This service answers that question for all of DevBoard.

It handles sign-up, login, logout, email checks and password reset. It gives users a **JWT** (a signed pass) that every other service trusts.

- **Port:** `8001`
- **Stack:** FastAPI, PostgreSQL, Redis, Alembic

---

## Start here (about 5 minutes)

1. Open a terminal in `devboard-infra`.
2. Run `setup.bat`. It creates the database and starts this service.
3. Open `http://localhost:8001/health`. You should see `{"status": "ok"}`.

Only want this one service? The database and Redis must already be running. Then:

```bash
docker compose up --build -d
docker compose exec devboard-auth alembic upgrade head
```

---

## What it does

1. **Sign up** – saves the user, sends a "verify your email" mail.
2. **Log in** – checks email and password, returns an access token and a refresh token.
3. **Keep you logged in** – swaps a refresh token for a new pair.
4. **Log out** – kills one refresh token, or all of them.
5. **Reset a password** – sends a reset link by email.

It also lets other services (only core, today) change a user's **role** or **active** status.

---

## How it fits

```
Browser ──> devboard-auth ──> devboard-email   (sends the mails)
                 │
                 ├──> devboard-core            (creates the user profile after sign-up)
                 ├──> PostgreSQL               (users and tokens)
                 └──> Redis                    (rate limits)

devboard-core ──X-Service-Key──> devboard-auth  (change role / status)
```

---

## Tokens

| Token | Lives for | Notes |
|---|---|---|
| Access token (JWT) | 5 minutes | Holds user id, email and role. Signed with `JWT_SECRET`. |
| Refresh token | 7 days | Random string. Only its hash is stored. Each refresh gives you a new one. |
| Email verification | 1 day | One use. |
| Password reset | 60 minutes | One use. |

---

## API

Public routes. Base path: `/auth`. Every path ends with `/`.

| Method | Path | What it does |
|---|---|---|
| `POST` | `/auth/register/` | Create an account. Password: 8 to 128 characters. |
| `POST` | `/auth/login/` | Get `access_token` and `refresh_token`. |
| `POST` | `/auth/refresh-token/` | Send `refresh_token`, get a new pair. |
| `POST` | `/auth/logout/` | Send `refresh_token`. Revokes that one token. |
| `POST` | `/auth/logout-all/` | Send `refresh_token`. Revokes every token of that user. |
| `GET` | `/auth/verify-email/?token=...` | Confirm the email link. |
| `POST` | `/auth/resend-verification/` | Send the verify mail again. |
| `POST` | `/auth/forgot-password/` | Send a reset mail. Always answers 200, so nobody can test which emails exist. |
| `POST` | `/auth/reset-password/` | Send `token` and new password. Logs the user out everywhere. |

Internal routes. Need the header `X-Service-Key`.

| Method | Path | What it does |
|---|---|---|
| `PATCH` | `/internal/users/{user_id}/status/` | Activate or deactivate a user. Deactivating also revokes all their tokens. |
| `PATCH` | `/internal/users/{user_id}/role/` | Set the role to `admin` or `member`. |

Health checks: `GET /health` and `GET /health/db`.

---

## Rate limits

Stored in Redis. If Redis is down, these routes return an error instead of running without limits.

| Route | Limit |
|---|---|
| Register | 10 per hour, per IP |
| Login | 5 per 15 minutes, per IP **and** per email |
| Resend verification | 3 per hour per IP, 10 per hour per email |
| Forgot password | 3 per hour per IP, 10 per hour per email |

A good login clears the login counters.

---

## Settings

Copy `.env.example` to `.env`, then fill it in.

| Variable | What it is |
|---|---|
| `DATABASE_URL` | Database link for the app (`postgresql+asyncpg://...`). |
| `DATABASE_URL_SYNC` | Database link for Alembic (`postgresql+psycopg2://...`). |
| `AUTH_DB_PASSWORD` | Read by `devboard-infra\setup.bat` to create the database user. Must match the password in the two URLs. |
| `JWT_SECRET` | Signs the tokens. Same value in every service. |
| `INTERNAL_API_KEY` | Shared key for service-to-service calls. |
| `FRONTEND_URL` | Base URL used in email links. |
| `EMAIL_SERVICE_URL` | Where devboard-email lives. |
| `CORE_SERVICE_URL` | Where devboard-core lives. |
| `REDIS_URL` | In Docker use `redis://devboard-redis:6379/0`. |
| `TRUSTED_PROXY_IPS` | Optional. Comma list of proxies whose `X-Forwarded-For` header can be trusted. |

Optional with defaults: `ACCESS_TOKEN_EXPIRE_MINUTES` (5), `REFRESH_TOKEN_EXPIRE_DAYS` (7), `VERIFICATION_TOKEN_EXPIRE_DAYS` (1), `PASSWORD_RESET_TOKEN_EXPIRE_MINUTES` (60).

---

## Database

Four tables: `users`, `refresh_tokens`, `verification_tokens`, `password_reset_tokens`.

```bash
alembic upgrade head                            # apply migrations
alembic revision --autogenerate -m "message"    # make a new one
```

---

## Good to know

- **Sign-up needs devboard-core.** If core is down, sign-up fails and the new user is deleted again.
- **Login needs a verified and active user.**
- **Users get the `member` role** by default.
