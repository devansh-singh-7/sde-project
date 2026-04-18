from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.routes import auth, chat, upload
from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.rate_limit import limiter

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up the application...")
    await init_db()
    yield
    print("Shutting down the application...")
    await close_db()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="AI-powered Document & Multimedia Q&A API",
    lifespan=lifespan,
)

# SlowAPI Rate Limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration
origins = [
    "http://localhost:5173",  # React/Vue standard dev frontend port
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(upload.router, prefix="/api/v1/upload", tags=["Upload"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])

from fastapi.staticfiles import StaticFiles
import os

# Mount uploads directory to serve static files (like media and pdfs)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

@app.get("/")
async def root():
    return {"message": "Welcome to the AI-powered Document & Multimedia Q&A API"}
