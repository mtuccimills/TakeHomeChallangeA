FROM python:3.13-slim

# Install uv (fast, matches your local toolchain)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency manifests first for layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies into the image (no dev deps for production)
RUN uv sync --frozen

# Copy the rest of the application
COPY . .

# uv puts the venv at /app/.venv; put it on PATH so `alembic`/`uvicorn` resolve
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000