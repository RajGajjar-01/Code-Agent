# Railway Deployment Guide - WordPress Agent

This comprehensive guide explains how to deploy your WordPress Agent application (FastAPI backend + React frontend) on Railway. It covers Railway architecture, Docker concepts, and step-by-step deployment instructions.

---

## Table of Contents

1. [What is Railway?](#what-is-railway)
2. [How Railway Works](#how-railway-works)
3. [Key Concepts](#key-concepts)
4. [Prerequisites](#prerequisites)
5. [Project Structure](#project-structure)
6. [Step-by-Step Deployment](#step-by-step-deployment)
7. [Environment Variables](#environment-variables)
8. [Networking](#networking)
9. [Database Setup](#database-setup)
10. [Domain Configuration](#domain-configuration)
11. [Monitoring & Logs](#monitoring--logs)
12. [Troubleshooting](#troubleshooting)
13. [Best Practices](#best-practices)

---

## What is Railway?

Railway is a **Platform-as-a-Service (PaaS)** that simplifies cloud deployment. Think of it as a modern alternative to Heroku, designed for developers who want to deploy quickly without managing servers.

### Why Railway?

| Feature | Traditional VPS | Railway |
|---------|-----------------|---------|
| Server Management | You manage everything | Zero management |
| Scaling | Manual configuration | Automatic |
| SSL Certificates | Manual setup | Automatic |
| CI/CD | Set up yourself | Built-in |
| Database Setup | Install & configure | One-click |
| Pricing | Fixed monthly | Pay for what you use |

### Railway vs Other Platforms

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLOUD DEPLOYMENT OPTIONS                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Traditional Cloud (AWS, GCP, Azure)                            │
│  ├── Maximum control                                            │
│  ├── Steep learning curve                                       │
│  ├── Pay for idle resources                                     │
│  └── Best for: Large enterprises, complex infrastructure        │
│                                                                  │
│  Container Platforms (Kubernetes, Docker Swarm)                 │
│  ├── Container orchestration                                     │
│  ├── Requires DevOps expertise                                  │
│  ├── High operational overhead                                  │
│  └── Best for: Teams with DevOps resources                      │
│                                                                  │
│  Platform-as-a-Service (Railway, Render, Fly.io)                │
│  ├── Zero infrastructure management                             │
│  ├── Git-based deployment                                       │
│  ├── Usage-based pricing                                        │
│  └── Best for: Startups, solo developers, quick deployments     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## How Railway Works

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         RAILWAY ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   YOUR CODE                                                              │
│   ┌──────────────────┐                                                   │
│   │ GitHub Repo      │                                                   │
│   │ - Dockerfile     │                                                   │
│   │ - Source Code    │                                                   │
│   └────────┬─────────┘                                                   │
│            │                                                             │
│            ▼                                                             │
│   RAILWAY BUILD SYSTEM                                                   │
│   ┌──────────────────┐                                                   │
│   │ 1. Pull Code     │                                                   │
│   │ 2. Detect Build  │                                                   │
│   │ 3. Build Image   │                                                   │
│   │ 4. Push to Reg.  │                                                   │
│   └────────┬─────────┘                                                   │
│            │                                                             │
│            ▼                                                             │
│   RAILWAY RUNTIME (Google Cloud Platform)                               │
│   ┌──────────────────────────────────────────────────────────────┐      │
│   │                                                               │      │
│   │   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐        │      │
│   │   │  Frontend   │   │   Backend   │   │  Postgres   │        │      │
│   │   │  Container  │   │  Container  │   │  Container  │        │      │
│   │   │   (nginx)   │   │  (FastAPI)  │   │             │        │      │
│   │   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘        │      │
│   │          │                 │                 │               │      │
│   │          │   Private Network (No Egress Fees)│               │      │
│   │          └─────────────────┬─────────────────┘               │      │
│   │                            │                                 │      │
│   └────────────────────────────┼──────────────────────────────────┘      │
│                                │                                         │
│                                ▼                                         │
│   RAILWAY NETWORKING                                                     │
│   ┌──────────────────┐                                                   │
│   │ Load Balancer    │                                                   │
│   │ SSL Termination  │                                                   │
│   │ Auto-scaling     │                                                   │
│   └────────┬─────────┘                                                   │
│            │                                                             │
│            ▼                                                             │
│   PUBLIC INTERNET                                                        │
│   https://your-app.up.railway.app                                       │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### The Deployment Pipeline

Railway follows this pipeline for every deployment:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        DEPLOYMENT PIPELINE                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. SOURCE DETECTION                                                    │
│     ├── GitHub: Webhook triggers on push                                │
│     ├── CLI: `railway up` uploads code                                  │
│     └── Image: Pull from Docker Hub                                     │
│                                                                          │
│  2. BUILD PHASE                                                         │
│     ├── Detect Dockerfile (named "Dockerfile" with capital D)           │
│     ├── Execute Docker build with layer caching                         │
│     ├── Inject build-time environment variables                         │
│     └── Push image to Railway's container registry                      │
│                                                                          │
│  3. DEPLOY PHASE                                                        │
│     ├── Pull image from registry                                        │
│     ├── Create container with resource limits                           │
│     ├── Inject runtime environment variables                            │
│     ├── Configure networking (private + optional public)                │
│     └── Start container with health checks                              │
│                                                                          │
│  4. RUNTIME PHASE                                                       │
│     ├── Health monitoring                                               │
│     ├── Log streaming to dashboard                                      │
│     ├── Auto-restart on failure                                         │
│     └── Horizontal scaling (if configured)                              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### What Happens When You Push Code?

1. **GitHub Webhook**: Railway receives a notification that you pushed to your repo
2. **Build Triggered**: Railway starts a new build for the affected service(s)
3. **Docker Build**: 
   - Railway pulls your code
   - Executes your Dockerfile instructions
   - Each `RUN`, `COPY`, etc. creates a cached layer
   - Final image is tagged and stored
4. **Deployment**:
   - Old container is gracefully shut down
   - New container starts with the new image
   - Health check passes → traffic routed to new container
   - Old container is terminated

---

## Key Concepts

### Services

A **Service** is a single deployable unit in Railway. Each service runs in its own container.

```
Project: wordpress-agent
├── Service: frontend (nginx container)
├── Service: backend (FastAPI container)
└── Service: postgres (PostgreSQL container)
```

### Projects

A **Project** is a collection of related services. All services in a project can communicate via private networking.

### Environments

Railway supports multiple environments per project:
- **Production**: Your live application
- **Staging**: Pre-production testing
- **Development**: Development environment

Each environment has its own:
- Services
- Variables
- Databases
- Domains

### Volumes

**Volumes** provide persistent storage for containers. Essential for databases!

```
Without Volume:
┌─────────────┐
│  Container  │ ── restart ──► Data Lost!
│  /data      │
└─────────────┘

With Volume:
┌─────────────┐     ┌─────────────┐
│  Container  │────►│   Volume    │
│  /data      │     │  (persist)  │
└─────────────┘     └─────────────┘
       │                   │
       └── restart ───────► Data Preserved!
```

### Variables

Railway provides several types of variables:

| Type | Scope | Use Case |
|------|-------|----------|
| **Service Variables** | Single service | API keys, secrets |
| **Shared Variables** | All services in environment | Common config |
| **Reference Variables** | Dynamic references | Service URLs |
| **Railway Variables** | Auto-provided | `RAILWAY_PUBLIC_DOMAIN`, `PORT` |

---

## Prerequisites

Before deploying, ensure you have:

### 1. Railway Account

```bash
# Sign up at railway.app
# Or use GitHub OAuth for quick setup
```

### 2. Railway CLI (Optional but Recommended)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Verify installation
railway version
```

### 3. GitHub Repository

Your code should be in a GitHub repository. Railway connects directly to GitHub for automatic deployments.

### 4. Local Testing

Test your Dockerfiles locally before deploying:

```bash
# Backend
cd backend
docker build -t wordpress-backend .
docker run -p 8000:8000 --env-file .env wordpress-backend

# Frontend
cd frontend
docker build -t wordpress-frontend .
docker run -p 80:80 wordpress-frontend
```

---

## Project Structure

Your project should have this structure:

```
Wordpress/
├── backend/
│   ├── Dockerfile              # Backend container definition
│   ├── .dockerignore           # Exclude files from build
│   ├── app/                    # FastAPI application
│   │   ├── main.py             # Entry point
│   │   ├── api/                # Routes
│   │   ├── core/               # Config
│   │   └── ...
│   ├── alembic/                # Database migrations
│   ├── pyproject.toml          # Python dependencies
│   └── uv.lock                 # Lock file
│
├── frontend/
│   ├── Dockerfile              # Frontend container (multi-stage)
│   ├── .dockerignore           # Exclude files from build
│   ├── nginx.conf              # nginx configuration
│   ├── src/                    # React application
│   ├── package.json            # Node dependencies
│   └── vite.config.ts          # Vite configuration
│
├── railway-deployment-guide.md # This file
└── README.md
```

---

## Step-by-Step Deployment

### Step 1: Create Railway Project

1. Go to [railway.app](https://railway.app)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Authorize Railway to access your GitHub
5. Select your `Wordpress` repository

### Step 2: Deploy PostgreSQL Database

Since you want to use a custom PostgreSQL container:

**Option A: Deploy from docker-compose**

1. In your Railway project, click **"Add Service"**
2. Select **"GitHub Repo"**
3. Choose your repository
4. Set **Root Directory** to `/backend` (where docker-compose.yml is)
5. Railway will detect the `db` service from docker-compose

**Option B: Use Railway's PostgreSQL Template (Recommended)**

1. Click **"Add Service"**
2. Select **"Database"** → **"PostgreSQL"**
3. Railway creates a managed PostgreSQL with:
   - Automatic backups
   - Connection pooling
   - Built-in monitoring

### Step 3: Deploy Backend Service

1. Click **"Add Service"** → **"GitHub Repo"**
2. Select your repository
3. Configure the service:
   - **Service Name**: `backend`
   - **Root Directory**: `/backend`
   - **Watch Path**: `backend/` (for auto-deploy)

4. Railway will:
   - Detect `Dockerfile` in `/backend`
   - Build the image
   - Deploy the container

### Step 4: Deploy Frontend Service

1. Click **"Add Service"** → **"GitHub Repo"**
2. Select your repository
3. Configure the service:
   - **Service Name**: `frontend`
   - **Root Directory**: `/frontend`
   - **Watch Path**: `frontend/` (for auto-deploy)

4. Railway will:
   - Detect `Dockerfile` in `/frontend`
   - Build the multi-stage image
   - Deploy nginx container

### Step 5: Configure Environment Variables

See [Environment Variables](#environment-variables) section for detailed configuration.

### Step 6: Run Database Migrations

After backend is deployed and database is ready:

```bash
# Using Railway CLI
railway run --service backend alembic upgrade head

# Or via Railway dashboard
# Settings → Commands → Add start command:
# alembic upgrade head && gunicorn app.main:app ...
```

### Step 7: Verify Deployment

1. Check service health in Railway dashboard
2. Visit your frontend URL: `https://frontend-xxx.up.railway.app`
3. Test backend health: `https://backend-xxx.up.railway.app/health`

---

## Environment Variables

### Understanding Variable Types

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ENVIRONMENT VARIABLE TYPES                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  SERVICE VARIABLES (Private to one service)                             │
│  ┌─────────────────────────────────────────────┐                        │
│  │ Service: backend                             │                        │
│  │ ├── GROQ_API_KEY=sk-xxx                     │                        │
│  │ ├── GOOGLE_CLIENT_SECRET=xxx                │                        │
│  │ └── APP_SECRET_KEY=xxx                      │                        │
│  └─────────────────────────────────────────────┘                        │
│                                                                          │
│  REFERENCE VARIABLES (Dynamic, auto-updating)                           │
│  ┌─────────────────────────────────────────────┐                        │
│  │ Service: backend                             │                        │
│  │ DATABASE_URL = ${{Postgres.DATABASE_URL}}   │                        │
│  │ FRONTEND_ORIGIN = ${{Frontend.RAILWAY_PUBLIC_DOMAIN}}│              │
│  └─────────────────────────────────────────────┘                        │
│                                                                          │
│  RAILWAY-PROVIDED VARIABLES (Automatic)                                 │
│  ├── RAILWAY_PUBLIC_DOMAIN      → frontend-xxx.up.railway.app          │
│  ├── RAILWAY_PRIVATE_DOMAIN     → frontend.railway.internal            │
│  ├── PORT                       → 8000 (or whatever you set)            │
│  └── RAILWAY_ENVIRONMENT        → production                           │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Backend Variables

Configure these in the Railway dashboard under **backend** → **Variables**:

```bash
# =============================================================================
# DATABASE CONNECTION
# =============================================================================
# Reference the PostgreSQL service's connection string
# Railway provides DATABASE_URL automatically if using Railway's Postgres

# If using custom PostgreSQL container:
DATABASE_URL=postgresql+asyncpg://${{Postgres.POSTGRES_USER}}:${{Postgres.POSTGRES_PASSWORD}}@${{Postgres.RAILWAY_PRIVATE_DOMAIN}}:5432/${{Postgres.POSTGRES_DB}}

# If using Railway's PostgreSQL template:
DATABASE_URL=${{Postgres.DATABASE_URL}}

# =============================================================================
# APPLICATION SETTINGS
# =============================================================================
# CORS - Allow requests from frontend
FRONTEND_ORIGIN=https://${{Frontend.RAILWAY_PUBLIC_DOMAIN}}

# Secret key for JWT tokens (GENERATE A SECURE KEY!)
# Run: python -c "import secrets; print(secrets.token_urlsafe(48))"
APP_SECRET_KEY=your-generated-secret-key-here

# =============================================================================
# LLM PROVIDER API KEYS
# =============================================================================
GROQ_API_KEY=your-groq-api-key
# GOOGLE_API_KEY=your-google-api-key  # If using Gemini

# =============================================================================
# GOOGLE OAUTH
# =============================================================================
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
# Update redirect URI to use Railway domain
GOOGLE_REDIRECT_URI=https://${{Backend.RAILWAY_PUBLIC_DOMAIN}}/api/auth/callback

# =============================================================================
# WORDPRESS CONNECTOR ENCRYPTION
# =============================================================================
# Generate Fernet key: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
WP_CONNECTOR_FERNET_KEYS=your-fernet-key

# =============================================================================
# OPTIONAL SETTINGS
# =============================================================================
LOG_LEVEL=INFO
```

### Frontend Variables

Configure these in the Railway dashboard under **frontend** → **Variables**:

```bash
# =============================================================================
# BUILD-TIME VARIABLES
# =============================================================================
# These are passed as build args (ARG in Dockerfile)
# They're embedded into the JavaScript bundle at build time

# Backend API URL for direct API calls
# Note: nginx proxies /api requests, but this is for the VITE_API_BASE_URL env
VITE_API_BASE_URL=https://${{Backend.RAILWAY_PUBLIC_DOMAIN}}
```

### Setting Variables in Railway Dashboard

1. Click on your service (e.g., `backend`)
2. Go to **Variables** tab
3. Click **"Add Variable"**
4. For reference variables, type `${{` to see autocomplete options
5. Railway will show available services and their variables

### Setting Variables via CLI

```bash
# Set a variable
railway variables set GROQ_API_KEY=sk-xxx --service backend

# Set multiple variables
railway variables set \
  GROQ_API_KEY=sk-xxx \
  APP_SECRET_KEY=secret \
  --service backend

# View all variables
railway variables --service backend
```

---

## Networking

### Public vs Private Networking

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      RAILWAY NETWORKING                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  PUBLIC NETWORKING                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                                                                  │   │
│  │   Internet ──► Railway Load Balancer ──► Your Container         │   │
│  │                    (HTTPS)                (HTTP)                │   │
│  │                                                                  │   │
│  │   Features:                                                      │   │
│  │   ├── Automatic SSL/TLS termination                            │   │
│  │   ├── *.up.railway.app domain                                   │   │
│  │   ├── Custom domain support                                     │   │
│  │   └── Billed for egress (outbound traffic)                      │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  PRIVATE NETWORKING                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                                                                  │   │
│  │   Frontend ──► Backend ──► Postgres                             │   │
│  │   (internal)   (internal)   (internal)                          │   │
│  │                                                                  │   │
│  │   Features:                                                      │   │
│  │   ├── Zero egress fees                                          │   │
│  │   ├── Faster latency                                            │   │
│  │   ├── Not accessible from internet                              │   │
│  │   └── Use RAILWAY_PRIVATE_DOMAIN                                │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Service Discovery

Services can reference each other using:

```bash
# Private domain (recommended for internal communication)
${{ServiceName.RAILWAY_PRIVATE_DOMAIN}}

# Public domain (for external access or cross-project)
${{ServiceName.RAILWAY_PUBLIC_DOMAIN}}

# Port
${{ServiceName.PORT}}
```

### nginx Configuration for Private Networking

The nginx.conf in frontend uses private networking:

```nginx
upstream backend {
    # Private networking - no egress fees, faster
    server backend.railway.internal:8000;
}
```

This means:
- Frontend → Backend communication is private
- No charges for internal traffic
- Lower latency

---

## Database Setup

### Option 1: Railway's Managed PostgreSQL (Recommended)

**Benefits:**
- Automatic backups
- Connection pooling
- One-click setup
- Automatic updates

**Steps:**
1. Click **"Add Service"** → **"Database"** → **"PostgreSQL"**
2. Railway creates the database with default credentials
3. `DATABASE_URL` is automatically available to other services

### Option 2: Custom PostgreSQL Container

Using your `docker-compose.yml`:

1. Create a separate service for PostgreSQL
2. Add a **Volume** for data persistence
3. Configure environment variables

**Railway Configuration:**

```yaml
# In Railway dashboard, configure PostgreSQL service:
# Service Name: postgres
# Root Directory: /backend (if docker-compose is there)

# Variables:
POSTGRES_USER=wordpress_agent
POSTGRES_PASSWORD=secure-password-here
POSTGRES_DB=wordpress_agent_db

# Add Volume:
# Mount Path: /var/lib/postgresql/data
# This persists your database data
```

### Running Migrations

After deploying, run Alembic migrations:

```bash
# Via Railway CLI
railway run --service backend alembic upgrade head

# Or add to your Dockerfile CMD:
# CMD alembic upgrade head && gunicorn app.main:app ...
```

---

## Domain Configuration

### Default Railway Domain

Each service gets a default domain:
```
https://your-service-abc123.up.railway.app
```

### Custom Domain

1. Go to **Settings** → **Domains**
2. Click **"Add Domain"**
3. Enter your domain (e.g., `app.yourdomain.com`)
4. Add the provided DNS records to your domain:
   ```
   CNAME app.yourdomain.com → your-service.up.railway.app
   ```
5. Railway automatically provisions SSL

### Domain Strategy for Full-Stack App

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       DOMAIN STRATEGY                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Option 1: Subdomains                                                    │
│  ├── app.yourdomain.com     → Frontend (React)                         │
│  └── api.yourdomain.com     → Backend (FastAPI)                        │
│                                                                          │
│  Option 2: Single Domain with nginx Proxy                               │
│  └── yourdomain.com         → Frontend                                 │
│      └── /api/*             → Proxied to Backend                       │
│                                                                          │
│  Option 3: Railway Default Domains                                      │
│  ├── frontend-xxx.up.railway.app                                       │
│  └── backend-xxx.up.railway.app                                        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Monitoring & Logs

### Viewing Logs

**Dashboard:**
1. Click on your service
2. Go to **Logs** tab
3. Real-time log streaming

**CLI:**
```bash
# View logs for a service
railway logs --service backend

# Follow logs (live)
railway logs --service backend --follow
```

### Health Checks

Your Dockerfiles include health checks:

**Backend:**
```dockerfile
HEALTHCHECK CMD curl --fail http://localhost:${PORT:-8000}/health || exit 1
```

**Frontend:**
```dockerfile
HEALTHCHECK CMD wget --spider http://localhost/ || exit 1
```

Railway uses these to:
- Monitor container health
- Restart unhealthy containers
- Route traffic only to healthy instances

### Metrics

Railway provides:
- CPU usage
- Memory usage
- Network I/O
- Request count

Access in **Metrics** tab of each service.

---

## Troubleshooting

### Common Issues

#### 1. Build Fails: "Dockerfile not found"

**Cause:** Dockerfile must be named exactly `Dockerfile` (capital D)

**Solution:**
```bash
# Wrong
mv Dockerfile dockerfile  # lowercase won't be detected

# Correct
mv dockerfile Dockerfile
```

#### 2. Build Fails: "Cannot find module"

**Cause:** Dependencies not installed or cached incorrectly

**Solution:**
- Check `package-lock.json` exists
- Ensure `.dockerignore` doesn't exclude lock files
- Try rebuilding without cache: Railway → Service → Settings → Rebuild

#### 3. Service Unhealthy

**Cause:** Health check failing

**Debug:**
```bash
# Check logs
railway logs --service backend

# Common issues:
# - Port not exposed correctly
# - Application error on startup
# - Missing environment variables
```

#### 4. CORS Errors

**Cause:** `FRONTEND_ORIGIN` not set correctly

**Solution:**
```bash
# In backend variables
FRONTEND_ORIGIN=https://${{Frontend.RAILWAY_PUBLIC_DOMAIN}}
```

#### 5. Database Connection Failed

**Cause:** Wrong `DATABASE_URL` or database not ready

**Debug:**
```bash
# Check if database is running
# Verify DATABASE_URL format
# Ensure database service is healthy

# Correct format for asyncpg:
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database
```

#### 6. Environment Variables Not Applied

**Cause:** Variables set after deployment

**Solution:**
- After changing variables, click **"Redeploy"**
- Or push a new commit to trigger rebuild

### Debugging Commands

```bash
# SSH into container (if enabled)
railway shell --service backend

# Run one-off commands
railway run --service backend python -c "from app.core.config import settings; print(settings)"

# Check environment
railway run --service backend env

# Test database connection
railway run --service backend python -c "import asyncio; from sqlalchemy.ext.asyncio import create_async_engine; asyncio.run(create_async_engine('your-url').connect())"
```

---

## Best Practices

### Security

1. **Never commit secrets** to Git
2. **Use sealed variables** for sensitive data in Railway
3. **Run as non-root user** (configured in Dockerfiles)
4. **Enable HTTPS only** (Railway does this automatically)
5. **Set strong secret keys**:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

### Performance

1. **Use multi-stage builds** (frontend Dockerfile)
2. **Optimize layer caching** (copy dependencies first)
3. **Use private networking** for service-to-service communication
4. **Enable gzip compression** (nginx.conf)
5. **Set appropriate cache headers** (nginx.conf)

### Reliability

1. **Add health checks** (in Dockerfiles)
2. **Configure proper timeouts**
3. **Use volumes for databases**
4. **Set up monitoring alerts**
5. **Test locally before deploying**

### Cost Optimization

1. **Use private networking** (no egress fees)
2. **Right-size your containers** (adjust memory/CPU limits)
3. **Use auto-sleep** for non-production environments
4. **Monitor usage** in Railway dashboard

### Development Workflow

```bash
# Local development with Railway variables
railway run --service backend uvicorn app.main:app --reload

# Connect to production database locally
railway connect postgres

# View all services status
railway status

# Open Railway dashboard
railway open
```

---

## Quick Reference

### Railway CLI Commands

```bash
railway login              # Login to Railway
railway init               # Initialize new project
railway up                 # Deploy current directory
railway status             # Show project status
railway logs               # View logs
railway variables          # Manage variables
railway run <cmd>          # Run command in service
railway shell              # Open shell in service
railway connect <service>  # Connect to database
railway open               # Open dashboard
```

### Useful Links

- [Railway Documentation](https://docs.railway.app)
- [Railway Discord](https://discord.gg/railway)
- [Railway Status](https://status.railway.app)
- [Railway Templates](https://railway.app/templates)

---

## Summary

You've created:

| File | Purpose |
|------|---------|
| `backend/Dockerfile` | Production-ready FastAPI container |
| `backend/.dockerignore` | Excludes unnecessary files from build |
| `frontend/Dockerfile` | Multi-stage build for React + nginx |
| `frontend/nginx.conf` | nginx config for SPA + API proxy |
| `frontend/.dockerignore` | Excludes unnecessary files from build |

Deployment steps:
1. Create Railway project
2. Deploy PostgreSQL (managed or custom)
3. Deploy Backend service
4. Deploy Frontend service
5. Configure environment variables
6. Run database migrations
7. Verify deployment

Your architecture:
```
Internet → Railway Load Balancer (HTTPS)
              │
              ├── Frontend (nginx:80)
              │     ├── Serves React static files
              │     └── Proxies /api/* → Backend
              │
              ├── Backend (FastAPI:8000)
              │     └── Connects to PostgreSQL
              │
              └── PostgreSQL (5432)
                    └── Persistent storage via volume
```
