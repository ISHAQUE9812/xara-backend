import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routes import auth
from app.database.db import connect_to_mongo, close_mongo_connection, get_db
from app.websocket.manager import manager
from app.ads import routes as ads_routes
from app.campaigns import routes as campaign_routes
from app.screens import routes as screen_routes
from app.websocket import screen_socket
from app.screens.playback_engine import playback_engine
from app.routes import analytics_routes
from app.routes import user_routes
from app.auth.role_middleware import require_authenticated_user
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="XARA Smart Signage API",
    description="FastAPI backend with JWT authentication and RBAC for XARA",
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
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(ads_routes.router, prefix="/media", tags=["Media"])
app.include_router(ads_routes.router, prefix="/ads", tags=["Advertisements"])
app.include_router(campaign_routes.router, prefix="/campaigns", tags=["Campaigns"])
app.include_router(screen_routes.router, prefix="/screens", tags=["Screens"])
app.include_router(screen_socket.router, prefix="/ws", tags=["WebSockets"])
app.include_router(analytics_routes.router, prefix="/analytics", tags=["Analytics"])
app.include_router(user_routes.router, prefix="/users", tags=["User Management"])

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

os.makedirs("media", exist_ok=True)
app.mount("/media", StaticFiles(directory="media"), name="media")


# Reports endpoint as requested by user specifications
@app.get("/reports", tags=["Reports"])
async def get_reports_api(
    current_user: dict = Depends(require_authenticated_user),
    db=Depends(get_db)
):
    # Standard users see their own campaign reports, admins see all
    pipeline = []
    if current_user.get("role") != "admin":
        cursor = db["campaigns"].find({"user_id": current_user["id"]})
        campaigns = await cursor.to_list(length=1000)
        campaign_ids = [c["campaign_id"] for c in campaigns]
        pipeline.append({"$match": {"campaign_id": {"$in": campaign_ids}}})
        
    pipeline.append({
        "$group": {
            "_id": None,
            "total_plays": {"$sum": "$play_count"},
            "total_impressions": {"$sum": "$impressions"},
            "avg_engagement": {"$avg": "$engagement_score"},
            "total_audience": {"$sum": "$audience_count"}
        }
    })
    
    result = await db["analytics"].aggregate(pipeline).to_list(1)
    if result:
        return {
            "success": True,
            "report": {
                "total_plays": result[0]["total_plays"],
                "total_impressions": result[0]["total_impressions"],
                "avg_engagement": round(result[0]["avg_engagement"], 2) if result[0]["avg_engagement"] else 0.0,
                "total_audience": result[0]["total_audience"]
            }
        }
    return {
        "success": True,
        "report": {
            "total_plays": 0,
            "total_impressions": 0,
            "avg_engagement": 0.0,
            "total_audience": 0
        }
    }

# Startup / shutdown events
@app.on_event("startup")
async def startup_event():
    logger.info("Connecting to MongoDB...")
    await connect_to_mongo()
    db = get_db()
    # Provide DB reference to websocket manager for status updates
    manager.set_db(db)
    logger.info("MongoDB connection established and manager wired.")
    
    # Start playback engine
    await playback_engine.start()

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Closing MongoDB connection...")
    await playback_engine.stop()
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
