import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from groq import AsyncGroq
from pydantic import BaseModel

from .scraper import download_landing_page_assets
from .tools import TOOL_DEFINITIONS, execute_tool
from .wordpress import WordPressClient

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

WP_BASE_URL = os.getenv("WP_BASE_URL", "")
WP_USERNAME = os.getenv("WP_USERNAME", "")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD", "")

FRONTEND_DIR = Path(__file__).parent.parent.parent / "frontend"

SYSTEM_PROMPT = """You are a helpful WordPress Agent. Be conversational and concise.

Only call tools when the user explicitly asks you to perform a WordPress action such as:
- Creating, updating, listing, or deleting pages/posts
- Uploading media files
- Getting site information

IMPORTANT RULES:
- Never call delete_page or delete_post directly. Always call list_pages or list_posts FIRST to get correct IDs, then delete.
- For greetings, questions, or general chat, reply directly without calling any tools.
- When building landing pages, include: Hero, Services, Trust indicators, CTA, Testimonials, and Contact sections."""

wp_client: Optional[WordPressClient] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global wp_client
    if WP_BASE_URL and WP_USERNAME and WP_APP_PASSWORD:
        wp_client = WordPressClient(WP_BASE_URL, WP_USERNAME, WP_APP_PASSWORD)
    yield
    if wp_client:
        await wp_client.close()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    chat_id: Optional[str] = None
    history: Optional[list[ChatMessage]] = []

class ChatResponse(BaseModel):
    response: str
    tool_calls: Optional[list[dict]] = []
    chat_id: Optional[str] = None

class ScrapeRequest(BaseModel):
    url: str
    output_dir: Optional[str] = None

@app.get("/health")
async def health():
    return {
        "status": "running",
        "groq": bool(GROQ_API_KEY),
        "wp": bool(wp_client),
    }

@app.post("/api/scrape")
async def scrape_assets(request: ScrapeRequest):
    """Download assets from a landing page URL."""
    result = await download_landing_page_assets(request.url, request.output_dir)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not set")

    groq_client = AsyncGroq(api_key=GROQ_API_KEY)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if request.history:
        for msg in request.history:
            messages.append({"role": msg.role, "content": msg.content})

    messages.append({"role": "user", "content": request.message})
    tool_calls_executed = []

    try:
        response = await groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
        )

        assistant_message = response.choices[0].message

        while assistant_message.tool_calls:
            messages.append({
                "role": "assistant",
                "content": assistant_message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in assistant_message.tool_calls
                ],
            })

            for tool_call in assistant_message.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)
                result = await execute_tool(func_name, func_args, wp_client)

                tool_calls_executed.append({
                    "name": func_name,
                    "arguments": func_args,
                    "result": result,
                    "status": "error" if "error" in result else "success",
                })

                messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": json.dumps(result)})

            response = await groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                tools=TOOL_DEFINITIONS,
            )
            assistant_message = response.choices[0].message

        return ChatResponse(
            response=assistant_message.content or "Done.",
            tool_calls=tool_calls_executed,
            chat_id=request.chat_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
