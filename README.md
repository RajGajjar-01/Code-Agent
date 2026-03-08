# Coding Agent Platform

A full-stack, extensible **coding agent** platform with a modern React UI and a FastAPI backend.

WordPress is one of the current integrations (site management, content operations, menus, WP-CLI automation), but the core goal is a reusable agent runtime that can be extended with additional tools and providers.

## What it does

- **Chat-driven coding workflows** via an authenticated API and UI
- **Tool-using agent runtime** (LLM-provider configurable)
- **Integrations** (currently WordPress + Google Drive) with room to add more
- **Conversation persistence** (history stored and retrievable)

## Getting Started

Follow these steps to set up and run the project locally.

### 1. Backend Setup (FastAPI)

The backend provides the agent runtime, integrations (WordPress, Google Drive, etc.), and database management.

1.  **Navigate to the backend directory**:
    ```bash
    cd backend
    ```

2.  **Install dependencies** using `uv` (recommended):
    ```bash
    uv sync
    ```

3.  **Set up the environment**:
    Create a `.env` file in the `backend/` directory (refer to `.env.example` if available).

4.  **Run migrations**:
    ```bash
    uv run alembic upgrade head
    ```

5.  **Start the development server**:
    ```bash
    uv run fastapi dev app/main.py
    ```
    The API will be available at `http://localhost:8000`.

### 2. Frontend Setup (React)

The frontend is a modern React application with shadcn/ui.

1.  **Navigate to the frontend directory**:
    ```bash
    cd frontend
    ```

2.  **Install dependencies**:
    ```bash
    npm install
    ```

3.  **Start the development server**:
    ```bash
    npm run dev
    ```
    The application will be available at `http://localhost:5173`.

---

## API Keys & Credentials

To fully use the agent, configure external services in `backend/.env`.

### 1. Google OAuth & Drive
Used for connecting Google Drive to browse and use files.
- **Get Keys**: [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
- **Required**: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`
- **Scopes**: Ensure you enable the Google Drive API.

### 2. Groq Cloud (LLM)
Powers the AI agent's logic and responses.
- **Get Keys**: [GroqCloud Console](https://console.groq.com/keys)
- **Required**: `GROQ_API_KEY`

### 3. LLM Provider selection
The agent supports multiple providers (configured via env):

- **Select provider**: `LLM_PROVIDER` (`groq`, `glm5`, `gemini`)
- **Models**: `GROQ_MODEL`, `GLM5_MODEL`, `GEMINI_MODEL`

### 4. Google OAuth & Drive
Used for connecting Google Drive to browse and use files.

- **Get Keys**: [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
- **Required**: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`
- **Scopes**: Ensure you enable the Google Drive API.

### 5. WordPress Connection (optional integration)
Enables the agent to interact with WordPress sites when you need it.

- **Create credentials**: In WordPress, go to your user profile and create an **Application Password**.
- **How to connect**: Use the UI/API to add a WordPress site (base URL, username, application password) and then select it as Active when chatting/performing operations.

---

## Project Structure
- `/backend`: FastAPI application and AI agent logic.
- `/frontend`: React + Vite + Tailwind CSS frontend.
