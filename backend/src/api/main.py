from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from .routes import articles, sources
from ..services.supabase_client import SupabaseService

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    supabase = SupabaseService()
    app.state.supabase = supabase
    yield

app = FastAPI(
    title="AI News API",
    description="API for AI News Application",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for production
# Allow all origins in development, or specific origins in production
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
if allowed_origins == ["*"]:
    # If using wildcard, use it directly (not as a list)
    cors_origins = ["*"]
else:
    cors_origins = allowed_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(articles.router, prefix="/articles", tags=["articles"])
app.include_router(sources.router, prefix="/sources", tags=["sources"])

@app.get("/")
async def root():
    return {"message": "AI News API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

