import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routes import auth
from app.database.db import connect_to_mongo, close_mongo_connection, get_db
from app.websocket.manager import manager
import logging

# Load environment variables (handled in db and jwt utils)
# Ensure .env is loaded by those modules via dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="XARA Smart Signage API",
    description="FastAPI backend with JWT authentication for XARA",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration – allow frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (campaign videos, uploads, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Register routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# Startup / shutdown events – DB connection and websocket manager wiring
@app.on_event("startup")
async def startup_event():
    logger.info("Connecting to MongoDB...")
    await connect_to_mongo()
    db = get_db()
    # Provide DB reference to websocket manager for status updates
    manager.set_db(db)
    logger.info("MongoDB connection established and manager wired.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Closing MongoDB connection...")
    await close_mongo_connection()
    logger.info("MongoDB connection closed.")

# Simple health endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "message": "XARA backend is running",
        "websocket_connections": manager.get_connection_count(),
        "connected_screens": manager.get_connected_screens(),
    }

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to XARA Smart Signage API",
        "docs": "/docs",
        "auth": "/auth",
    }
