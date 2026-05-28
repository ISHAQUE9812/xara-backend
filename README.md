# XARA Smart Signage - Backend API

Enterprise AI-powered Smart Advertisement and Audience Intelligence platform backend.

## 🎯 Overview

XARA is a complete backend infrastructure for managing smart digital signage screens with:
- Real-time WebSocket synchronization
- AI-powered campaign decision engine
- Multi-screen campaign management
- Comprehensive analytics tracking
- UUID-based device management
- JWT authentication
- Offline cache support

## 🏗️ Architecture

```
Admin Dashboard
      ↓
Create Campaign
      ↓
Assign Screens (WebSocket Sync)
      ↓
Specific Screen Receives Campaign
      ↓
AI Audience Detection
      ↓
Campaign Decision Engine
      ↓
Play Video
      ↓
Analytics Sync to Cloud
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- MongoDB 4.0+
- pip

### Installation

1. Clone the repository:
```bash
cd d:\Ishaque\xara-backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Setup environment:
```bash
cp .env.example .env
# Edit .env with your MongoDB URL and secrets
```

5. Run the server:
```bash
python run.py
```

The API will be available at: `http://localhost:8000`

**API Documentation**: 
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 📋 API Endpoints

### Authentication
- `POST /auth/signup` - Register new user
- `POST /auth/login` - Login and get JWT token
- `GET /auth/me` - Get current user profile

### Screen Management
- `POST /screens/register` - Register new screen (generates UUID)
- `GET /screens` - Get all screens
- `GET /screens/online` - Get online screens only
- `GET /screens/{screen_id}` - Get screen details
- `PATCH /screens/{screen_id}` - Update screen
- `PATCH /screens/{screen_id}/status` - Update screen status
- `DELETE /screens/{screen_id}` - Delete screen

### Campaign Management
- `POST /campaigns` - Create new campaign
- `GET /campaigns` - Get all campaigns
- `GET /campaigns/active` - Get active campaigns
- `GET /campaigns/{campaign_id}` - Get campaign details
- `PATCH /campaigns/{campaign_id}` - Update campaign
- `POST /campaigns/{campaign_id}/assign-screens` - Assign to screens
- `POST /campaigns/{campaign_id}/play` - Trigger playback
- `DELETE /campaigns/{campaign_id}` - Delete campaign
- `POST /campaigns/{campaign_id}/archive` - Archive campaign

### Playback Control
- `GET /playback/{screen_id}/current-campaign` - Get current campaign
- `GET /playback/{screen_id}/trigger` - Trigger playback
- `POST /playback/{screen_id}/switch/{campaign_id}` - Switch campaign
- `POST /playback/{screen_id}/start-playback/{campaign_id}` - Record playback start
- `POST /playback/{screen_id}/end-playback/{campaign_id}` - Record playback end
- `GET /playback/{screen_id}/history` - Get playback history
- `GET /playback/{screen_id}/cached-videos` - Get cached videos

### Analytics
- `POST /analytics/` - Record analytics event
- `GET /analytics/screen/{screen_id}` - Get screen analytics
- `GET /analytics/campaign/{campaign_id}` - Get campaign analytics
- `GET /analytics/screen/{screen_id}/performance` - Screen performance metrics
- `GET /analytics/campaign/{campaign_id}/performance` - Campaign performance metrics
- `GET /analytics/top-campaigns` - Top campaigns by engagement
- `GET /analytics/top-screens` - Top screens by engagement
- `GET /analytics/screen/{screen_id}/hourly` - Hourly analytics
- `POST /analytics/sync-local` - Sync offline analytics

### AI & Intelligence
- `POST /ai/metadata` - Record AI metadata (emotion, audience, etc.)
- `GET /ai/screen/{screen_id}/metadata` - Get screen metadata
- `GET /ai/screen/{screen_id}/latest` - Get latest metadata
- `POST /ai/decide/{screen_id}` - AI Decision Engine
- `GET /ai/screen/{screen_id}/audience-insights` - Audience insights
- `GET /ai/screen/{screen_id}/emotion-distribution` - Emotion analytics
- `GET /ai/screen/{screen_id}/age-distribution` - Age group analytics

### WebSocket
- `ws://localhost:8000/ws/screens/{screen_id}` - Real-time screen communication

## 🔌 WebSocket Events

### Screen Events
```json
{
  "event": "screen_online",
  "screen_id": "SCREEN_001",
  "timestamp": "2026-05-27T12:00:00"
}
```

### Campaign Events
```json
{
  "event": "campaign_update",
  "screen_id": "SCREEN_001",
  "campaign": { ... }
}
```

```json
{
  "event": "campaign_play",
  "screen_id": "SCREEN_001",
  "video": "nike.mp4",
  "campaign_id": "...",
  "campaign_name": "Nike Campaign"
}
```

### Status Events
```json
{
  "event": "screen_status_update",
  "screen_id": "SCREEN_001",
  "status": "online"
}
```

## 🗄️ MongoDB Collections

### screens
```json
{
  "_id": ObjectId,
  "screen_id": "SCREEN_001",
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Mall Entrance Screen",
  "location": "Dubai Mall",
  "status": "online",
  "resolution": "1920x1080",
  "current_campaign": "campaign_id",
  "assigned_campaigns": ["campaign_id_1", "campaign_id_2"],
  "websocket_connected": true,
  "last_seen": "2026-05-27T12:00:00",
  "created_at": "2026-05-27T12:00:00",
  "updated_at": "2026-05-27T12:00:00"
}
```

### campaigns
```json
{
  "_id": ObjectId,
  "campaign_name": "Nike Campaign",
  "video_url": "/videos/nike.mp4",
  "assigned_screens": ["SCREEN_001", "SCREEN_003"],
  "targeting": {
    "emotion": "happy",
    "age_group": "18-25"
  },
  "status": "active",
  "created_by": "admin@xara.com",
  "play_count": 150,
  "impressions": 1250,
  "created_at": "2026-05-27T12:00:00",
  "updated_at": "2026-05-27T12:00:00"
}
```

## 🔐 Authentication

All protected endpoints require JWT token in Authorization header:

```
Authorization: Bearer <token>
```

Get token from login:
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'
```

## 🎯 Screen Registration Flow

1. Screen boots up
2. Generates UUID (uuid4)
3. Calls `POST /screens/register`
4. Receives screen_id and UUID
5. Connects to WebSocket: `ws://server/ws/screens/{screen_id}`
6. Listens for campaign updates
7. Downloads and plays videos
8. Sends analytics and AI metadata back

## 🤖 AI Decision Engine

The decision engine matches audience metadata with campaign targeting:

**Input**: Latest AI metadata
- emotion: "happy", "sad", "neutral", etc.
- age_group: "18-25", "25-35", etc.
- engagement_score: 0-100
- audience_count: number of people

## 📊 Tech Stack

- **Framework**: FastAPI
- **Database**: MongoDB with Motor Async Driver
- **Authentication**: JWT with bcrypt
- **Real-time**: WebSockets
- **Validation**: Pydantic
- **Deployment**: Uvicorn

## 🚀 Features Implemented

✅ UUID Screen Management
✅ Screen Registration with WebSocket
✅ Campaign Management & Assignment
✅ Screen-Specific Campaign Playback
✅ AI Metadata Processing
✅ AI Decision Engine
✅ Real-time WebSocket Sync
✅ Analytics Tracking
✅ Audience Intelligence
✅ Offline Cache Support
✅ JWT Authentication
✅ Multi-Screen Support
✅ Services Architecture
✅ Complete Async Implementation
✅ Production-Ready Error Handling

---

**XARA Smart Signage Backend v1.0** - Enterprise AI Infrastructure for Digital Signage
