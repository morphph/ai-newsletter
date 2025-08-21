from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from .routes import articles, sources, monitoring, tweets, content
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

# Configure CORS - allow all origins for now
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=False,  # Must be False when using wildcard
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(articles.router, prefix="/api/articles", tags=["articles"])
app.include_router(sources.router, prefix="/api/sources", tags=["sources"])
app.include_router(monitoring.router, prefix="/api/monitoring", tags=["monitoring"])
app.include_router(tweets.router, prefix="/api", tags=["tweets"])
app.include_router(content.router, prefix="/api", tags=["unified-content"])

@app.get("/")
async def root():
    return {"message": "AI News API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/debug/routes")
async def debug_routes():
    routes = []
    for route in app.routes:
        if hasattr(route, "path"):
            routes.append({
                "path": route.path,
                "methods": list(route.methods) if hasattr(route, "methods") else []
            })
    return {"routes": routes}

