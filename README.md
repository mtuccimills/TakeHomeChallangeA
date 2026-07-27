# Pokémon Trainer API

A RESTful API built with **FastAPI** for managing users and the Pokémon they capture. Each user can register, authenticate, and build their own collection of Pokémon. When a collection is retrieved, the API enriches every entry with the Pokémon's real name, fetched asynchronously from the public [PokéAPI](https://pokeapi.co/).

The application follows a layered **Clean Architecture** (controller → service → repository → entity), uses fully asynchronous database access, and ships with a containerized environment that provisions the database, runs migrations, and executes the test suite from a single command.

> **All requests that carry a body must be sent with the header `Content-Type: application/json`.** The only exception is the token endpoint (`POST /api/v1/users/token`), which expects `application/x-www-form-urlencoded` data as required by the OAuth2 password flow.

---

## Badges

[![CircleCI](https://dl.circleci.com/status-badge/img/gh/mtuccimills/TakeHomeChallangeA/tree/main.svg?style=svg&circle-token=CCIPRJ_4NDRbUyQMf5JWMqsB8hQFX_7c8706b28eaf239756a436e4c48685ee52e65c9c)](https://dl.circleci.com/status-badge/redirect/gh/mtuccimills/TakeHomeChallangeA/tree/main)

[![Coverage Status](https://coveralls.io/repos/github/mtuccimills/TakeHomeChallangeA/badge.svg?branch=main)](https://coveralls.io/github/mtuccimills/TakeHomeChallangeA?branch=main)

## Features

- **User management** — registration, listing, retrieval by id / email / username, full and partial updates, and deletion, with ownership enforcement so users can only modify their own account.
- **Authentication** — OAuth2 password flow issuing JWT bearer tokens; protected routes require a valid `Authorization: Bearer <token>` header.
- **Password change** — authenticated users can change their own password.
- **Pokémon collection** — capture, list, retrieve, update, and release (delete) Pokémon, each owned by the authenticating user.
- **External API enrichment** — Pokémon names are resolved live from the PokéAPI through a dedicated async client with connection pooling, in-memory caching, and concurrent batched lookups.
- **Pagination** — list endpoints support `skip` / `limit` query parameters with a `has_more` indicator.
- **Automatic schema management** — database migrations run automatically on startup via Alembic.
- **Interactive documentation** — auto-generated Swagger UI and ReDoc.

---

## Entities

| Entity                | Description                                            | Key fields                                                        |
| --------------------- | ----------------------------------------------------- | ----------------------------------------------------------------- |
| `User`                | An application user and Pokémon trainer.              | `id`, `username`, `email`, `password_hash`, `image_file`          |
| `Pokemon`             | A Pokémon captured by a user.                          | `id`, `pokemon_id`, `user_id`, `date_captured`                    |
| `PasswordResetToken`  | A short-lived, hashed token associated with a user.   | `id`, `user_id`, `token_hash`, `expires_at`, `created_at`         |

**Relationships:** a `User` owns many `Pokemon` (one-to-many) and many `PasswordResetToken` records. Each `Pokemon` and `PasswordResetToken` belongs to exactly one `User`.

---

## Author

**Matías Joaquín Tucci**

---

## Table of Contents

- [Technology](#technology)
- [Decisions made](#decisions-made)
- [Routes](#routes)
- [Pre-requisites](#pre-requisites)
- [Run App](#run-app)
- [Preload Data](#preload-data)
- [Run Tests](#run-tests)
- [Standards Applied](#standards-applied)
- [Deployment](#deployment)
- [Areas to improve](#areas-to-improve)

---

## Decisions made

- Clean Architecture: To be able to habdle further changess ie future in a proper way.
- UV: uv is a dependency manager that allows us to have a better segregation between our projects and improves speed compare to pip.
- SQLAlchemy: Because it is an ORM which is easy to use and has great documentation.
- Alembic: We've chosen to use alembic as the dependency to manage migrations since it's one of the most common libraries and has high documentation.
- Seed file: We've decided to manage seeding on a different file separated from alembic's migration to have properly separated the schema (structure) from the mock data.
- Docker: To make portabele the app
- Docker profiles: I decided to use a test profile on the docker-compose to prevent us from generating second docker-coompose file soley for testing purposes
- PyTest: Is the most common library for testing in python.
- E2E Test:  Testing was ddone E2E because we wanted to evaluate all parts of our clean architecture. We don't need to do unit test on every funtion of every file, a E2E test evaluating every endpoint is good enough.


## Technology

| Technology            | Purpose                                                        |
| --------------------- | ------------------------------------------------------------- |
| **Python 3.14**       | Language runtime.                                             |
| **FastAPI**           | Web framework and request/response validation.               |
| **SQLAlchemy (async)**| ORM with asynchronous database access.                       |
| **PostgreSQL**        | Relational database.                                         |
| **psycopg 3**         | Async PostgreSQL driver.                                     |
| **Alembic**           | Database schema migrations.                                  |
| **Pydantic v2 / pydantic-settings** | Data validation and environment-based configuration. |
| **PyJWT + Argon2** (`pwdlib`) | JWT authentication and password hashing.            |
| **httpx**             | Async HTTP client for the PokéAPI integration.              |
| **pytest + anyio**    | Asynchronous test suite.                                    |
| **Docker / Compose**  | Containerized build, database, migrations, and tests.       |
| **uv**                | Dependency management and packaging.                         |

---

## Routes

All routes are prefixed with `/api/v1`. Interactive documentation is available at `/docs` (Swagger UI) and `/redoc` once the app is running.

### Users — `/api/v1/users`

| Method   | Path                     | Auth | Description                                             |
| -------- | ------------------------ | :--: | ------------------------------------------------------ |
| `POST`   | `/`                      |  —   | Create a new user.                                     |
| `GET`    | `/`                      |  —   | List all users (public view).                          |
| `GET`    | `/{user_id}`             |  —   | Retrieve a single user by id (private view).           |
| `GET`    | `/email/{email}`         |  —   | Retrieve a user by email (public view).                |
| `GET`    | `/username/{username}`   |  —   | Retrieve a user by username (public view).             |
| `PUT`    | `/{user_id}`             |  ✔   | Full update of a user (owner only).                    |
| `PATCH`  | `/{user_id}`             |  ✔   | Partial update of a user (owner only).                 |
| `DELETE` | `/{user_id}`             |  ✔   | Delete a user (owner only).                            |
| `GET`    | `/me`                    |  ✔   | Retrieve the authenticated user.                       |
| `PATCH`  | `/me/password`           |  ✔   | Change the authenticated user's password.              |
| `POST`   | `/token`                 |  —   | Obtain a JWT access token (OAuth2, form-encoded body). |
| `GET`    | `/{user_id}/pokemon`     |  —   | List a user's captured Pokémon (name-enriched, paginated). |

### Pokémon — `/api/v1/pokemons`

| Method   | Path        | Auth | Description                                            |
| -------- | ----------- | :--: | ----------------------------------------------------- |
| `GET`    | `/`         |  —   | List all Pokémon (paginated, name-enriched).          |
| `GET`    | `/{id}`     |  —   | Retrieve a single Pokémon (name-enriched).            |
| `POST`   | `/`         |  ✔   | Capture a Pokémon for the authenticated user.         |
| `PUT`    | `/{id}`     |  ✔   | Full update of a Pokémon (owner only).                |
| `PATCH`  | `/{id}`     |  ✔   | Partial update of a Pokémon (owner only).             |
| `DELETE` | `/{id}`     |  ✔   | Release (delete) a Pokémon (owner only).              |

---

## Pre-requisites

- **[Docker](https://www.docker.com/)** and **Docker Compose** installed and running.
* SUDO is not needed

- Ports free: 8000, 5432
That is the only requirement to build and run the project — Docker provisions the database, the Python runtime, and all dependencies. No local Python or PostgreSQL installation is needed.

> For running the application or tests **outside** of Docker (optional), you additionally need Python 3.14, [uv](https://docs.astral.sh/uv/), and a local PostgreSQL instance.

---

## Run App

1. **Provide the environment file.** Copy the example and adjust values if needed:

   ```bash
   cp .env.example .env
   ```

2. **Build and start the stack:**

   ```bash
   docker compose up --build
   ```

   This starts PostgreSQL, waits until it is healthy, runs the database migrations, and then launches the API.

3. **Open the application:**

   - API base URL: <http://localhost:8000>
   - Swagger UI: <http://localhost:8000/docs>
   - ReDoc: <http://localhost:8000/redoc>

To run it in the background, add the `-d` flag: `docker compose up -d --build`.

To stop the stack:

```bash
docker compose down          # stop containers
docker compose down -v       # stop and remove the database volume (wipes all data)
```

---

## Preload Data

The database schema is created and kept up to date **automatically**. On startup, a dedicated `migrate` service runs `alembic upgrade head` against the application database *before* the API starts, ensuring the structure is always current. No manual migration step is required.

After generating the database, a second script is run to add the seed information. This information includes the following users for you to properly test the system and login functions:

| Username | Email               | Password     | Pokémon (by `pokemon_id`) |
| -------- | ------------------- | ------------ | ------------------------- |
| Ash      | ash@example.com     | pikachu123   | 25 (Pikachu), 1 (Bulbasaur) |
| Misty    | misty@example.com   | staryu123    | 120 (Staryu), 121 (Starmie) |

> Log in via `POST /api/v1/users/token` with the email as the username and the password above to obtain a JWT, then use it as a `Bearer` token on the authenticated routes.

A separate test database (`test_userdb`) is provisioned automatically the first time the PostgreSQL volume is created, via the `init-test-db.sql` initialization script mounted into the container.

> **Note:** the test-database initialization script only runs when the PostgreSQL data volume is created from scratch. If the test database is ever missing, recreate the volume with `docker compose down -v` followed by `docker compose up --build`.

---

## Run Tests

The test suite runs in its own one-shot container against the isolated test database. It is guarded behind a Compose **profile**, so it does not run during a normal `docker compose up`.

```bash
docker compose --profile test run --rm test
```

This provisions the database, runs the full `pytest` suite with verbose output, and removes the container afterward. The command exits with the test suite's exit code.

To run the tests locally (outside Docker), with a PostgreSQL instance available:

```bash
uv run pytest tests -v
```

---

## Standards Applied

- **Clean Architecture** — each feature is organized into clearly separated layers: `controller` (HTTP), `service` (business logic and authorization), `repository` (data access), and `entity` (schemas). External concerns such as the PokéAPI live in a dedicated `clients` layer.
- **Asynchronous end-to-end** — non-blocking I/O across the web layer, the database, and outbound HTTP calls.
- **Dependency injection** — database sessions and external clients are provided through FastAPI dependencies, enabling clean testing via overrides.
- **RESTful conventions** — resource-oriented routes, appropriate HTTP verbs, and accurate status codes (`201` on creation, `204` on deletion, `401` / `403` / `404` / `422` for error conditions).
- **Configuration via environment** — all settings are sourced from the environment through `pydantic-settings`, with separate configuration for development and testing.
- **Automated testing** — integration tests cover CRUD operations, authentication, authorization, validation, pagination, and external-API enrichment, with the external dependency mocked for isolation.
- **Linting & formatting** — code style is maintained with **Ruff**.

---

## Deployment

The application is deployed as a set of Docker Compose services:

- **`postgres`** — the PostgreSQL database, with a health check and a persistent named volume.
- **`migrate`** — a one-shot service that applies Alembic migrations once the database is healthy, then exits. The application only starts after this completes successfully.
- **`app`** — the FastAPI application, served by Uvicorn on port `8000`.
- **`test`** — a one-shot service (behind the `test` profile) that runs the test suite against an isolated test database.

Configuration is supplied through environment variables (`.env` for the application, `.env.test` for local test runs), keeping credentials and connection details out of the codebase and the built image.

For a production deployment, the recommended adjustments are: supply strong secrets through the platform's secret manager rather than a committed file, remove the published `5432` database port so PostgreSQL is only reachable on the internal network, and run the `app` service behind a reverse proxy (e.g. Nginx or a managed load balancer) with TLS termination.


## Areas to improve

- Generic method should be used to mock endpoints.
- We could add user routes for forgotten password via email.
- Error handling could be improved (prevent 500 errors)
- Deployment could be done



