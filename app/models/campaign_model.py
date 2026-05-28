from datetime import datetime
from typing import Optional, Dict, Any, List


class CampaignModel:
    @staticmethod
    def create_document(campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format the campaign data for MongoDB insertion."""
        now = datetime.utcnow()
        video_url = campaign_data.get("video_url", "")
        return {
            "campaign_name": campaign_data.get("campaign_name"),
            "video_url": video_url,
            "video_filename": campaign_data.get("video_filename") or (video_url.split('/')[-1] if video_url else None),
            "description": campaign_data.get("description"),
            "objective": campaign_data.get("objective"),
            "priority": campaign_data.get("priority", 1),
            "budget": campaign_data.get("budget", 0.0),
            "duration": campaign_data.get("duration", 30),
            "assigned_screens": campaign_data.get("assigned_screens", []),
            "targeting": campaign_data.get("targeting") or {},
            "status": campaign_data.get("status", "draft"),
            "created_by": campaign_data.get("created_by"),
            "created_at": now,
            "updated_at": now,
            "start_date": campaign_data.get("start_date"),
            "end_date": campaign_data.get("end_date"),
            "start_time": campaign_data.get("start_time"),
            "end_time": campaign_data.get("end_time"),
            "play_count": 0,
            "impressions": 0,
        }

    @staticmethod
    def format_response(campaign: Dict[str, Any]) -> Dict[str, Any]:
        """Format MongoDB document to API response schema."""
        if not campaign:
            return {}
        campaign["id"] = str(campaign.pop("_id"))
        # Generate media_url from video_url for static file serving
        video_url = campaign.get("video_url", "")
        if video_url and not video_url.startswith("http"):
            campaign["media_url"] = f"http://localhost:8000/static/uploads/campaigns/{video_url}"
        else:
            campaign["media_url"] = video_url
        return campaign


class AnalyticsModel:
    @staticmethod
    def create_document(analytics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format the analytics data for MongoDB insertion."""
        now = datetime.utcnow()
        return {
            "screen_id": analytics_data.get("screen_id"),
            "campaign_id": analytics_data.get("campaign_id"),
            "play_count": analytics_data.get("play_count", 0),
            "impressions": analytics_data.get("impressions", 0),
            "engagement_score": analytics_data.get("engagement_score", 0),
            "audience_count": analytics_data.get("audience_count", 0),
            "duration_watched": analytics_data.get("duration_watched", 0),
            "timestamp": now,
        }

    @staticmethod
    def format_response(analytics: Dict[str, Any]) -> Dict[str, Any]:
        """Format MongoDB document to API response schema."""
        if not analytics:
            return {}
        analytics["id"] = str(analytics.pop("_id"))
        return analytics


class AIMetadataModel:
    @staticmethod
    def create_document(metadata_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format the AI metadata for MongoDB insertion."""
        now = datetime.utcnow()
        return {
            "device_id": metadata_data.get("device_id"),
            "screen_id": metadata_data.get("screen_id"),
            "emotion": metadata_data.get("emotion"),
            "age_group": metadata_data.get("age_group"),
            "audience_count": metadata_data.get("audience_count", 0),
            "engagement_score": metadata_data.get("engagement_score", 0),
            "detected_objects": metadata_data.get("detected_objects", []),
            "timestamp": now,
        }

    @staticmethod
    def format_response(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Format MongoDB document to API response schema."""
        if not metadata:
            return {}
        metadata["id"] = str(metadata.pop("_id"))
        return metadata
