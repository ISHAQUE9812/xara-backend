# XARA Backend - Development Guide

## Environment Setup

### Prerequisites
- Python 3.9+
- MongoDB 4.0+
- pip or conda
- Git

### 1. Clone Repository
```bash
git clone <repository-url>
cd xara-backend
```

### 2. Setup Virtual Environment

**On Linux/Mac:**
```bash
bash setup.sh
```

**On Windows:**
```bash
setup.bat
```

**Manual Setup:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 3. Configure Environment

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` with your settings:
```
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=xara_db
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=3000
ENVIRONMENT=development
DEBUG=True
```

### 4. Start MongoDB

**Using Docker:**
```bash
docker run -d -p 27017:27017 --name xara-mongo mongo:6.0
```

**Or locally:**
```bash
mongod
```

### 5. Run the Server

```bash
python run.py
```

Server starts at: `http://localhost:8000`

## API Testing

### 1. Swagger UI Documentation
Visit: `http://localhost:8000/docs`

### 2. Using curl

**Register a User:**
```bash
curl -X POST "http://localhost:8000/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@xara.com",
    "username": "admin",
    "full_name": "Admin User",
    "password": "securepassword123"
  }'
```

**Login:**
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@xara.com",
    "password": "securepassword123"
  }'
```

**Register Screen:**
```bash
curl -X POST "http://localhost:8000/screens/register" \
  -H "Content-Type: application/json" \
  -d '{
    "screen_id": "SCREEN_001",
    "name": "Mall Entrance",
    "location": "Dubai Mall",
    "resolution": "1920x1080"
  }'
```

**Create Campaign:**
```bash
curl -X POST "http://localhost:8000/campaigns/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_name": "Nike Summer Sale",
    "video_url": "/videos/nike.mp4",
    "video_filename": "nike.mp4",
    "duration": 30,
    "assigned_screens": ["SCREEN_001"],
    "targeting": {
      "emotion": "happy",
      "age_group": "18-25"
    },
    "status": "active"
  }'
```

**Get Current Campaign for Screen:**
```bash
curl -X GET "http://localhost:8000/playback/SCREEN_001/current-campaign" \
  -H "Content-Type: application/json"
```

### 3. Using Python Requests

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# Login
response = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "admin@xara.com",
    "password": "securepassword123"
})
token = response.json()["access_token"]

# Register Screen
requests.post(f"{BASE_URL}/screens/register", json={
    "screen_id": "SCREEN_001",
    "name": "Mall Entrance",
    "location": "Dubai Mall",
    "resolution": "1920x1080"
})

# Create Campaign
requests.post(
    f"{BASE_URL}/campaigns/",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "campaign_name": "Nike Campaign",
        "video_url": "/videos/nike.mp4",
        "duration": 30,
        "assigned_screens": ["SCREEN_001"]
    }
)

# Record AI Metadata
requests.post(f"{BASE_URL}/ai/metadata", json={
    "device_id": "SCREEN_001",
    "screen_id": "SCREEN_001",
    "emotion": "happy",
    "audience_count": 5,
    "engagement_score": 82
})

# Get Screen Analytics
analytics = requests.get(f"{BASE_URL}/analytics/screen/SCREEN_001")
print(analytics.json())
```

## Code Structure

### Models
- **ScreenModel**: Screen data structure and formatting
- **CampaignModel**: Campaign data and database operations
- **AnalyticsModel**: Analytics event structure
- **AIMetadataModel**: AI sensor data

### Services
- **ScreenService**: Screen registration, status, management
- **CampaignService**: Campaign CRUD and assignment
- **PlaybackService**: Video playback logic and history
- **AnalyticsService**: Analytics recording and aggregation
- **AIService**: AI decision engine and insights

### Routes
- **auth_routes.py**: User authentication
- **screen_routes.py**: Screen management endpoints
- **campaign_routes.py**: Campaign endpoints
- **playback_routes.py**: Video playback endpoints
- **analytics_routes.py**: Analytics endpoints
- **ai_routes.py**: AI decision engine endpoints

### Database
- **MongoDB Collections**:
  - `screens`: Screen devices
  - `campaigns`: Campaign data
  - `ai_metadata`: AI sensor readings
  - `analytics`: Analytics events
  - `users`: User accounts

## Development Workflow

### Adding a New Feature

1. **Create Schema** (if needed) in `app/schemas/`
2. **Create/Update Model** in `app/models/`
3. **Create/Update Service** in `app/services/`
4. **Create/Update Route** in `app/routes/`
5. **Add to main.py** if new route file
6. **Test via Swagger UI** at `/docs`

### Example: Adding a new endpoint

**1. Schema** (`app/schemas/campaign_schema.py`):
```python
class CustomSchema(BaseModel):
    field1: str
    field2: int
```

**2. Service** (`app/services/campaign_service.py`):
```python
async def new_method(self, param):
    # Implementation
    return result
```

**3. Route** (`app/routes/campaign_routes.py`):
```python
@router.get("/new-endpoint")
async def new_endpoint(service: CampaignService = Depends(get_campaign_service)):
    result = await service.new_method(param)
    return result
```

## Testing

### Run all tests:
```bash
pytest tests/
```

### Run specific test:
```bash
pytest tests/test_screens.py
```

### With coverage:
```bash
pytest --cov=app tests/
```

## Docker Development

Build image:
```bash
docker build -t xara-api .
```

Run with Docker Compose:
```bash
docker-compose up -d
```

## Troubleshooting

### MongoDB Connection Error
- Ensure MongoDB is running: `mongosh` or check Docker container
- Check MONGODB_URL in .env
- Verify network connectivity

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill process (Linux/Mac)
kill -9 <PID>

# Or use different port in run.py
```

### Import Errors
- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`
- Check Python path: `python -c "import sys; print(sys.path)"`

### WebSocket Connection Issues
- Check if screen_id is being passed correctly
- Verify WebSocket URL format: `ws://localhost:8000/ws/screens/{screen_id}`
- Check browser console for connection errors

## Performance Tips

1. **Database Indexing**: Add indexes to frequently queried fields
2. **Connection Pooling**: Motor handles this automatically
3. **Caching**: Consider Redis for frequently accessed data
4. **Batch Operations**: Use bulk insert/update for large operations
5. **Async**: Always use async/await for I/O operations

## Security Checklist

- [ ] Change SECRET_KEY in production
- [ ] Use strong database passwords
- [ ] Enable HTTPS in production
- [ ] Implement rate limiting
- [ ] Validate all inputs
- [ ] Use environment variables for secrets
- [ ] Implement CORS properly
- [ ] Add API key authentication for devices

## Next Steps

1. Deploy to production server
2. Set up CI/CD pipeline
3. Add comprehensive logging
4. Implement monitoring and alerting
5. Add API rate limiting
6. Set up automated backups for MongoDB
7. Add email notifications for events
8. Create admin dashboard

---

For more information, see [README.md](README.md)
