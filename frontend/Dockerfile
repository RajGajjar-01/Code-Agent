# =============================================================================
# FRONTEND DOCKERFILE - React + Vite Application with nginx
# =============================================================================
# This Dockerfile uses MULTI-STAGE BUILD to create an optimized production image.
# Multi-stage builds allow you to use multiple FROM statements in one Dockerfile.
# Each FROM begins a new "stage" of the build.
#
# WHY MULTI-STAGE?
# -----------------------------------------------------------------------------
# Stage 1 (builder): Has Node.js, npm, source code, dev dependencies (~500MB)
# Stage 2 (production): Only has nginx + compiled static files (~25MB)
#
# Benefits:
# - 95% smaller final image (25MB vs 500MB)
# - No source code in production image (security)
# - No dev dependencies (smaller attack surface)
# - Faster deployments (smaller image to push/pull)
# =============================================================================

# =============================================================================
# STAGE 1: BUILDER - Build the React Application
# =============================================================================
# This stage compiles your React/Vite application into static files.
# After this stage completes, we throw away everything except the build output.

FROM node:22-alpine AS builder

# -----------------------------------------------------------------------------
# Build Arguments (Available during build only)
# -----------------------------------------------------------------------------
# ARG defines variables passed at build time with --build-arg.
# These are used to inject environment-specific values into the build.
#
# Railway provides these automatically during build:
# - RAILWAY_SERVICE_NAME
# - RAILWAY_ENVIRONMENT
# - RAILWAY_PROJECT_ID
#
# VITE_API_BASE_URL:
# - Vite embeds environment variables starting with VITE_ into the build
# - This tells the frontend where to find the backend API
# - At runtime, nginx will proxy /api requests, but we need this for direct calls
# -----------------------------------------------------------------------------

ARG RAILWAY_SERVICE_NAME
ARG RAILWAY_ENVIRONMENT
ARG RAILWAY_PROJECT_ID

# VITE_API_BASE_URL will be passed from Railway environment
ARG VITE_API_BASE_URL

# -----------------------------------------------------------------------------
# Working Directory
# -----------------------------------------------------------------------------
# /app is the standard convention for application directories.
# All subsequent commands run from this directory.

WORKDIR /app

# -----------------------------------------------------------------------------
# Copy Package Files (Layer Caching Optimization)
# -----------------------------------------------------------------------------
# Copy package.json and lock file BEFORE source code.
# This allows Docker to cache the npm install layer if dependencies haven't changed.
#
# Why does this matter?
# - npm install can take 1-3 minutes
# - If you only change src/ code, Docker skips npm install entirely
# - This saves significant build time during development

COPY package.json package-lock.json ./

# -----------------------------------------------------------------------------
# Install Dependencies
# -----------------------------------------------------------------------------
# npm ci (Clean Install):
# - Installs exact versions from package-lock.json
# - Faster than npm install (no version resolution needed)
# - Reproducible builds (same versions every time)
# - Deletes node_modules before installing (clean slate)
#
# --ignore-scripts: Skips package lifecycle scripts (security + speed)
# - Some packages run post-install scripts that can be slow or malicious
# - We don't need them for building
#
# Alternative: npm install
# - Would resolve latest compatible versions
# - Not recommended for production (inconsistent builds)

RUN npm ci --ignore-scripts

# -----------------------------------------------------------------------------
# Copy Source Code
# -----------------------------------------------------------------------------
# Now copy the rest of the application.
# This invalidates the cache only when source files change.

COPY . .

# -----------------------------------------------------------------------------
# Set Build-Time Environment Variables
# -----------------------------------------------------------------------------
# ENV sets environment variables for subsequent commands.
# Vite uses these during the build process.
#
# VITE_* variables are embedded into the JavaScript bundle at build time.
# This is different from runtime environment variables!
# - Build-time: Baked into the code, can't change without rebuilding
# - Runtime: Can be changed without rebuilding (requires server config)
#
# For SPAs, build-time variables are common because:
# - Static files are served directly (no server to read env vars)
# - nginx serves pre-built files
#
# Note: ${VITE_API_BASE_URL:-http://localhost:8000} uses default if not provided

ENV VITE_API_BASE_URL=${VITE_API_BASE_URL:-http://localhost:8000}

# -----------------------------------------------------------------------------
# Build the Application
# -----------------------------------------------------------------------------
# npm run build executes the "build" script from package.json.
# For Vite projects, this:
# 1. Runs TypeScript compiler (tsc -b)
# 2. Bundles all JavaScript/CSS with Vite
# 3. Optimizes and minifies the output
# 4. Generates static files in ./dist/ directory
#
# Output structure:
# dist/
# ├── index.html          # Entry point
# ├── assets/
# │   ├── index-[hash].js # Bundled JavaScript
# │   ├── index-[hash].css # Bundled CSS
# │   └── [other-assets]
# └── [other-files]

RUN npm run build

# =============================================================================
# STAGE 2: PRODUCTION - nginx Server
# =============================================================================
# This is the final stage that will be deployed.
# We start fresh from a minimal nginx image and copy ONLY the built files.
# Everything from the builder stage is discarded.

FROM nginx:1.27-alpine AS production

# -----------------------------------------------------------------------------
# Build Arguments (for labeling)
# -----------------------------------------------------------------------------

ARG RAILWAY_SERVICE_NAME
ARG RAILWAY_ENVIRONMENT

# -----------------------------------------------------------------------------
# Labels (Metadata)
# -----------------------------------------------------------------------------
# LABEL adds metadata to the image.
# Useful for organization, searching, and documentation.

LABEL maintainer="WordPress Agent Team" \
      service="${RAILWAY_SERVICE_NAME:-frontend}" \
      environment="${RAILWAY_ENVIRONMENT:-production}"

 # Default backend URL for local runs. On Railway, set BACKEND_URL as a service
 # variable (ideally referencing backend via private networking).
 ENV BACKEND_URL=http://backend.railway.internal:8000

# -----------------------------------------------------------------------------
# Remove Default nginx Configuration
# -----------------------------------------------------------------------------
# nginx comes with a default configuration that:
# - Serves a welcome page
# - Doesn't match our application's needs
#
# We remove it and replace with our custom config.

RUN rm /etc/nginx/conf.d/default.conf

# -----------------------------------------------------------------------------
# Copy Custom nginx Configuration
# -----------------------------------------------------------------------------
# COPY copies files from the build context into the container.
# We copy our custom nginx.conf that:
# - Serves the React SPA
# - Proxies /api requests to the backend
# - Handles client-side routing
# - Adds security headers

 # nginx official image supports envsubst templates placed under
 # /etc/nginx/templates/*.template. These are rendered at container start using
 # environment variables.
 COPY nginx.conf /etc/nginx/templates/default.conf.template

# -----------------------------------------------------------------------------
# Copy Built Static Files
# -----------------------------------------------------------------------------
# COPY --from=builder copies from a previous build stage!
# This is the key feature of multi-stage builds.
#
# --from=builder: Specifies which stage to copy from
# /app/dist/: Source path in the builder stage
# /usr/share/nginx/html/: Destination in this stage
#
# nginx serves files from /usr/share/nginx/html by default.
# This is where our compiled React app will live.

COPY --from=builder /app/dist /usr/share/nginx/html

# -----------------------------------------------------------------------------
# Create nginx Runtime Directories
# -----------------------------------------------------------------------------
# nginx needs these directories for:
# - /var/cache/nginx: Caching proxy responses
# - /var/log/nginx: Access and error logs
# - /var/run: PID file location
#
# We create them with proper permissions for the nginx user.

RUN mkdir -p /var/cache/nginx /var/log/nginx /var/run && \
    chown -R nginx:nginx /var/cache/nginx /var/log/nginx /var/run && \
    chown -R nginx:nginx /usr/share/nginx/html

# -----------------------------------------------------------------------------
# Expose Port
# -----------------------------------------------------------------------------
# EXPOSE documents that the container listens on port 80.
# nginx listens on port 80 by default (HTTP).
#
# Railway:
# - Detects this and routes traffic to port 80
# - Provides HTTPS termination automatically
# - Assigns a *.up.railway.app domain

EXPOSE 80

# -----------------------------------------------------------------------------
# Health Check
# -----------------------------------------------------------------------------
# HEALTHCHECK tells Docker how to verify the container is healthy.
# Railway uses this for monitoring and automatic restarts.
#
# wget is used instead of curl because:
# - Alpine images have wget by default
# - curl would need to be installed separately
#
# --spider: Only check if page exists, don't download
# --quiet: Don't output progress
# --tries=1: Only try once
# --timeout=2: Wait max 2 seconds for response

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

# -----------------------------------------------------------------------------
# Start nginx
# -----------------------------------------------------------------------------
# CMD specifies the command to run when the container starts.
#
# nginx: The nginx server
# -g: Pass a global directive
# daemon off: Run in foreground (not as daemon)
#
# Why daemon off?
# - Docker containers need the main process to stay running
# - If nginx runs as daemon, it forks to background
# - The container would exit immediately
# - "daemon off" keeps nginx in foreground, container stays alive

CMD ["nginx", "-g", "daemon off;"]
