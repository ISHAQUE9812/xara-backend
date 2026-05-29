from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.database.db import get_db
from app.schemas.campaign_schema import AnalyticsCreate, AnalyticsResponse
from app.services.analytics_service import AnalyticsService
from app.auth.role_middleware import require_authenticated_user, require_admin
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_analytics_service(db=Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db)

@router.post("/", response_model=AnalyticsResponse)
async def record_analytics(
    analytics: AnalyticsCreate,
    current_user: dict = Depends(require_authenticated_user),
    service: AnalyticsService = Depends(get_analytics_service)
):
    analytics_data = analytics.dict()
    result = await service.record_analytics(analytics_data)
    return result

@router.get("", response_model=List[AnalyticsResponse])
@router.get("/", response_model=List[AnalyticsResponse])
async def get_user_analytics(
    current_user: dict = Depends(require_authenticated_user),
    db=Depends(get_db)
):
    # Standard user can only see their own campaign analytics
    if current_user.get("role") != "admin":
        cursor = db["campaigns"].find({"created_by": current_user["id"]})
        campaigns = await cursor.to_list(length=1000)
        campaign_ids = [str(c["_id"]) for c in campaigns]
        query = {"campaign_id": {"$in": campaign_ids}}
    else:
        query = {}
        
    cursor = db["analytics"].find(query).sort("timestamp", -1)
    analytics = await cursor.to_list(length=1000)
    for a in analytics:
        a["id"] = str(a.pop("_id"))
    return analytics

@router.get("/reports")
async def get_user_reports(
    current_user: dict = Depends(require_authenticated_user),
    db=Depends(get_db)
):
    pipeline = []
    if current_user.get("role") != "admin":
        cursor = db["campaigns"].find({"created_by": current_user["id"]})
        campaigns = await cursor.to_list(length=1000)
        campaign_ids = [str(c["_id"]) for c in campaigns]
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

# ============ ADMIN ONLY METRICS ============

@router.get("/global")
async def get_global_analytics(
    current_user: dict = Depends(require_admin),
    db=Depends(get_db)
):
    pipeline = [
        {
            "$group": {
                "_id": None,
                "total_plays": {"$sum": "$play_count"},
                "total_impressions": {"$sum": "$impressions"},
                "avg_engagement": {"$avg": "$engagement_score"},
                "total_audience": {"$sum": "$audience_count"}
            }
        }
    ]
    result = await db["analytics"].aggregate(pipeline).to_list(1)
    if result:
        return {
            "global_metrics": {
                "total_plays": result[0]["total_plays"],
                "total_impressions": result[0]["total_impressions"],
                "avg_engagement": round(result[0]["avg_engagement"], 2) if result[0]["avg_engagement"] else 0.0,
                "total_audience": result[0]["total_audience"]
            }
        }
    return {
        "global_metrics": {
            "total_plays": 0,
            "total_impressions": 0,
            "avg_engagement": 0.0,
            "total_audience": 0
        }
    }

@router.get("/screens")
async def get_screens_analytics(
    current_user: dict = Depends(require_admin),
    db=Depends(get_db)
):
    pipeline = [
        {
            "$group": {
                "_id": "$screen_id",
                "total_plays": {"$sum": "$play_count"},
                "total_impressions": {"$sum": "$impressions"},
                "avg_engagement": {"$avg": "$engagement_score"},
                "total_audience": {"$sum": "$audience_count"}
            }
        }
    ]
    result = await db["analytics"].aggregate(pipeline).to_list(100)
    return {
        "screens_metrics": [
            {
                "screen_id": r["_id"],
                "total_plays": r["total_plays"],
                "total_impressions": r["total_impressions"],
                "avg_engagement": round(r["avg_engagement"], 2) if r["avg_engagement"] else 0.0,
                "total_audience": r["total_audience"]
            } for r in result
        ]
    }

@router.get("/users")
async def get_users_analytics(
    current_user: dict = Depends(require_admin),
    db=Depends(get_db)
):
    # Aggregate campaign performance by creator (user)
    pipeline = [
        {
            "$lookup": {
                "from": "campaigns",
                "localField": "campaign_id",
                "foreignField": "_id", # Wait, campaign_id is stored as string in analytics
                "as": "campaign"
            }
        },
        {
            "$unwind": {
                "path": "$campaign",
                "preserveNullAndEmptyArrays": True
            }
        },
        {
            "$group": {
                "_id": "$campaign.created_by",
                "total_plays": {"$sum": "$play_count"},
                "total_impressions": {"$sum": "$impressions"},
                "avg_engagement": {"$avg": "$engagement_score"},
                "total_audience": {"$sum": "$audience_count"}
            }
        }
    ]
    
    # Wait, because campaign_id in analytics might be string while campaigns uses ObjectId. Let's do a robust cross-collection match:
    # First get all campaigns and map created_by to campaign_ids
    cursor = db["campaigns"].find({})
    campaigns = await cursor.to_list(length=1000)
    campaign_user_map = {str(c["_id"]): c.get("created_by", "unknown") for c in campaigns}
    
    cursor = db["analytics"].find({})
    analytics_records = await cursor.to_list(length=10000)
    
    user_metrics = {}
    for a in analytics_records:
        camp_id = a.get("campaign_id")
        created_by = campaign_user_map.get(camp_id, "unknown")
        if created_by not in user_metrics:
            user_metrics[created_by] = {
                "total_plays": 0,
                "total_impressions": 0,
                "engagements": [],
                "total_audience": 0
            }
        user_metrics[created_by]["total_plays"] += a.get("play_count", 0)
        user_metrics[created_by]["total_impressions"] += a.get("impressions", 0)
        user_metrics[created_by]["total_audience"] += a.get("audience_count", 0)
        if a.get("engagement_score") is not None:
            user_metrics[created_by]["engagements"].append(a["engagement_score"])
            
    response_list = []
    for user_id, metrics in user_metrics.items():
        engs = metrics["engagements"]
        avg_eng = round(sum(engs) / len(engs), 2) if engs else 0.0
        response_list.append({
            "user_id": user_id,
            "total_plays": metrics["total_plays"],
            "total_impressions": metrics["total_impressions"],
            "avg_engagement": avg_eng,
            "total_audience": metrics["total_audience"]
        })
        
    return {"users_metrics": response_list}
