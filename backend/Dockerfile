# =============================================================================
# BACKEND DOCKERFILE - FastAPI Application
# =============================================================================
# This Dockerfile creates a production-ready container for your FastAPI backend.
# Each section is explained in detail to help you understand deployment concepts.
# =============================================================================

# -----------------------------------------------------------------------------
# SECTION 1: BASE IMAGE SELECTION
# -----------------------------------------------------------------------------
# The FROM instruction specifies the base image to build upon.
# 
# Why python:3.14-slim-bookworm?
# - "slim" variants are minimal Debian-based images (smaller attack surface)
# - "bookworm" is the Debian version (stable, well-tested)
# - Size comparison: python:3.14 (~1GB) vs python:3.14-slim (~150MB)
# - Smaller images = faster builds, faster deploys, less storage cost
#
# Why not Alpine? Alpine uses musl libc instead of glibc, which can cause
# compatibility issues with Python packages (especially those with C extensions).
# -----------------------------------------------------------------------------

FROM python:3.14-slim-bookworm AS base

# -----------------------------------------------------------------------------
# SECTION 2: BUILD ARGUMENTS
# -----------------------------------------------------------------------------
# ARG defines variables that are available ONLY during the build process.
# These are NOT available at runtime (use ENV for runtime variables).
#
# Railway automatically provides these variables during build:
# - RAILWAY_SERVICE_NAME: The name of your service
# - RAILWAY_ENVIRONMENT: The environment (production, staging, etc.)
# - RAILWAY_PROJECT_ID: Your project's unique identifier
#
# You can use these for conditional build logic or debugging.
# -----------------------------------------------------------------------------

# Declare Railway-provided build arguments (optional, for reference)
ARG RAILWAY_SERVICE_NAME
ARG RAILWAY_ENVIRONMENT
ARG RAILWAY_PROJECT_ID

# -----------------------------------------------------------------------------
# SECTION 3: ENVIRONMENT VARIABLES (Build-time)
# -----------------------------------------------------------------------------
# ENV sets environment variables that persist in the container.
# These affect how Python behaves in production.
#
# PYTHONUNBUFFERED=1:
# - By default, Python buffers stdout/stderr output
# - In containers, you want logs to appear immediately
# - This ensures real-time log streaming to Railway dashboard
#
# PYTHONDONTWRITEBYTECODE=1:
# - Prevents Python from writing .pyc files (compiled bytecode)
# - Reduces image size and prevents stale cache issues
#
# PIP_NO_CACHE_DIR=1:
# - Disables pip cache (not needed in production)
# - Reduces image size significantly
#
# PIP_DISABLE_PIP_VERSION_CHECK=1:
# - Skips pip version check (faster builds, less noise)
# -----------------------------------------------------------------------------

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# -----------------------------------------------------------------------------
# SECTION 4: WORKING DIRECTORY
# -----------------------------------------------------------------------------
# WORKDIR sets the working directory for subsequent instructions.
# - Creates the directory if it doesn't exist
# - All relative paths will be relative to this directory
# - Using /app is a common convention (you could use anything)
#
# Why not use /? 
# - Organizes your application files separately from system files
# - Makes it clear where your application code lives
# -----------------------------------------------------------------------------

WORKDIR /app

# -----------------------------------------------------------------------------
# SECTION 5: INSTALL SYSTEM DEPENDENCIES
# -----------------------------------------------------------------------------
# RUN executes commands in the container and commits the results.
#
# Why do we need system dependencies?
# - Some Python packages require C libraries to compile
# - libpq-dev: Required for psycopg2/asyncpg (PostgreSQL drivers)
# - build-essential: GCC compiler for building Python extensions
# - curl: Useful for health checks and debugging
#
# Why apt-get update && apt-get install in one RUN?
# - Docker caches each layer separately
# - If we split them, apt-get update could be cached with stale package lists
# - Combining ensures fresh package lists every time packages change
#
# Why rm -rf /var/lib/apt/lists/*?
# - Cleans apt cache to reduce image size
# - These lists are only needed during package installation
# -----------------------------------------------------------------------------

RUN apt-get update && apt-get install -y --no-install-recommends \
    # PostgreSQL development headers (for asyncpg/psycopg2)
    libpq-dev \
    # Build tools for Python packages with C extensions
    build-essential \
    # Useful for health checks and HTTP requests
    curl \
    # Clean up apt cache to reduce image size
    && rm -rf /var/lib/apt/lists/*

# -----------------------------------------------------------------------------
# SECTION 6: INSTALL UV PACKAGE MANAGER
# -----------------------------------------------------------------------------
# UV is a modern Python package manager written in Rust.
# - 10-100x faster than pip
# - Resolves dependencies more efficiently
# - Compatible with pip and virtualenv
#
# Why use UV instead of pip?
# - Your project already uses uv (uv.lock file exists)
# - Faster builds = faster deployments on Railway
# - Better dependency resolution = fewer conflicts
#
# The COPY --from instruction copies from another image (multi-stage).
# We copy uv binary from the official astral/uv image.
# -----------------------------------------------------------------------------

# Copy uv binary from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# -----------------------------------------------------------------------------
# SECTION 7: COPY DEPENDENCY FILES (Layer Caching Optimization)
# -----------------------------------------------------------------------------
# Docker uses layer caching to speed up builds.
# Each instruction creates a layer that can be cached.
#
# Why copy pyproject.toml and uv.lock separately from source code?
# - If source code changes but dependencies don't, Docker uses cached layer
# - If we copied everything at once, ANY file change would invalidate cache
# - This optimization can save minutes on each build
#
# Order matters! Put frequently changing files (source code) last.
# -----------------------------------------------------------------------------

# Copy dependency files first (for better caching)
COPY pyproject.toml uv.lock ./

# -----------------------------------------------------------------------------
# SECTION 8: INSTALL PYTHON DEPENDENCIES
# -----------------------------------------------------------------------------
# uv sync installs dependencies from uv.lock:
# - Creates a virtual environment automatically
# - Installs exact versions from lock file (reproducible builds)
# - Much faster than pip install
#
# --frozen: Fails if uv.lock is out of date (ensures consistency)
# --no-dev: Skips dev dependencies (pytest, black, mypy, etc.)
#           This reduces image size and attack surface in production
# --no-install-project: Don't install the project itself yet
#           We'll install it after copying source for editable install
#
# Note: We don't use --no-dev here because your pyproject.toml has
# dev dependencies mixed with production. We filter later.
# -----------------------------------------------------------------------------

# Install dependencies using uv (fast!)
RUN uv sync --frozen --no-install-project

# Make sure CLI entrypoints installed into the uv virtual environment are on PATH.
# uv creates a venv at /app/.venv by default, so binaries live in /app/.venv/bin.
ENV PATH="/app/.venv/bin:${PATH}"

# -----------------------------------------------------------------------------
# SECTION 9: COPY APPLICATION SOURCE CODE
# -----------------------------------------------------------------------------
# Now copy the actual application code.
# This is done AFTER dependencies for better layer caching.
#
# The .dockerignore file excludes unnecessary files:
# - .venv/ (virtual environment - we create our own)
# - __pycache__/ (Python bytecode cache)
# - .pytest_cache/, htmlcov/ (test artifacts)
# - .git/ (git history - not needed in container)
# - *.pyc, *.pyo (compiled Python files)
# -----------------------------------------------------------------------------

# Copy application source code
COPY . .

# Install the project in editable mode
RUN uv sync --frozen

# -----------------------------------------------------------------------------
# SECTION 10: CREATE NON-ROOT USER (Security Best Practice)
# -----------------------------------------------------------------------------
# By default, containers run as root user.
# Running as non-root is a security best practice:
# - Limits potential damage if container is compromised
# - Many security scanners flag root containers
# - Required by some deployment platforms
#
# useradd flags:
# - --create-home: Creates home directory (/home/appuser)
# - --shell /bin/bash: Sets default shell
# - appuser: The username (you can choose any name)
#
# chown changes ownership of /app to appuser:
# - Required for the user to read/write files
# -----------------------------------------------------------------------------

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app

# -----------------------------------------------------------------------------
# SECTION 11: CREATE UPLOADS DIRECTORY
# -----------------------------------------------------------------------------
# Your application stores uploaded files in the uploads/ directory.
# We need to create it with proper permissions before switching users.
# -----------------------------------------------------------------------------

# Create uploads directory with proper permissions
RUN mkdir -p /app/uploads && chown -R appuser:appuser /app/uploads

# -----------------------------------------------------------------------------
# SECTION 12: SWITCH TO NON-ROOT USER
# -----------------------------------------------------------------------------
# USER sets the user for subsequent instructions and runtime.
# All commands after this will run as 'appuser'.
# -----------------------------------------------------------------------------

USER appuser

# -----------------------------------------------------------------------------
# SECTION 13: EXPOSE PORT (Documentation)
# -----------------------------------------------------------------------------
# EXPOSE documents which port the container listens on.
# - This is DOCUMENTATION only - it doesn't actually publish the port
# - Railway uses this to automatically configure port detection
# - The actual port binding happens at runtime
#
# Port 8000 is the default for FastAPI applications.
# Railway sets the PORT environment variable - we use it at runtime.
# -----------------------------------------------------------------------------

EXPOSE 8000

# -----------------------------------------------------------------------------
# SECTION 14: HEALTH CHECK
# -----------------------------------------------------------------------------
# HEALTHCHECK tells Docker how to verify the container is healthy.
# Railway uses this to determine if your service is running properly.
#
# --interval=30s: Check every 30 seconds
# --timeout=10s: Wait 10 seconds for response before failing
# --start-period=10s: Give app 10 seconds to start before first check
# --retries=3: Mark unhealthy after 3 consecutive failures
#
# Your app has a /health endpoint that returns status info.
# curl --fail returns non-zero exit code on HTTP errors.
# -----------------------------------------------------------------------------

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl --fail http://localhost:${PORT:-8000}/health || exit 1

# -----------------------------------------------------------------------------
# SECTION 15: DEFAULT COMMAND
# -----------------------------------------------------------------------------
# CMD specifies the default command to run when the container starts.
# This can be overridden at runtime.
#
# Why Gunicorn with Uvicorn workers?
# - Gunicorn is a production-grade WSGI/ASGI server
# - Uvicorn is an ASGI server optimized for async Python (FastAPI)
# - Combining them gives you:
#   - Multiple worker processes (utilize multiple CPU cores)
#   - Process management (auto-restart crashed workers)
#   - Graceful reloads
#
# Command breakdown:
# - gunicorn: The server
# - app.main:app: Module path to FastAPI instance (app/main.py -> app)
# - --workers: Number of worker processes
#   - Formula: (2 x CPU_cores) + 1
#   - Railway typically provides 1-2 cores, so 2-4 workers
# - --worker-class uvicorn.workers.UvicornWorker: Use async workers
# - --bind 0.0.0.0:${PORT:-8000}: Bind to Railway's dynamic port
#   - ${PORT:-8000} means: use PORT env var, or 8000 if not set
# - --timeout 120: Graceful timeout for worker shutdown
# - --access-logfile -: Log to stdout (Railway captures this)
# - --log-level info: Standard logging level
# -----------------------------------------------------------------------------

# Production server configuration
CMD ["gunicorn", "app.main:app", \
     "--workers", "2", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:${PORT:-8000}", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--log-level", "info"]
