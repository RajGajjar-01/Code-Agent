# Wordpress Agent

A powerful, full-stack AI agent built to manage WordPress sites, browse files, and facilitate content creation with a sleek React-based UI.

## 🚀 Getting Started

Follow these steps to set up and run the project locally.

### 1. Backend Setup (FastAPI)

The backend handles the AI logic, WordPress integration, and database management.

1.  **Navigate to the backend directory**:
    ```bash
    cd backend
    ```

2.  **Install dependencies** using `uv` (recommended):
    ```bash
    uv pip install -r requirements.txt
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

## 🔑 API Keys & Credentials

To fully use the agent, you will need to configure several external services in your backend `.env` file.

### 1. Google OAuth & Drive
Used for connecting Google Drive to browse and use files.
- **Get Keys**: [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
- **Required**: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`
- **Scopes**: Ensure you enable the Google Drive API.

### 2. Groq Cloud (LLM)
Powers the AI agent's logic and responses.
- **Get Keys**: [GroqCloud Console](https://console.groq.com/keys)
- **Required**: `GROQ_API_KEY`

### 3. WordPress Credentials
Enables the agent to interact with your WordPress site.
- **Configuration**: Go to your WordPress user profile and create an **Application Password**.
- **Required**: `WP_BASE_URL`, `WP_USERNAME`, `WP_APP_PASSWORD`

---

## 🏗️ Project Structure
- `/backend`: FastAPI application and AI agent logic.
- `/frontend`: React + Vite + Tailwind CSS frontend.
- `/knowledge`: Knowledge items for the agent.
