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
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(articles.router, prefix="/api/articles", tags=["articles"])
app.include_router(sources.router, prefix="/api/sources", tags=["sources"])

@app.get("/")
async def root():
    return {"message": "AI News API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}