#!/bin/bash
# XARA API Testing Script

BASE_URL="http://localhost:8000"

echo "=========================================="
echo "XARA Smart Signage API - Testing Script"
echo "=========================================="
echo ""

# Test 1: Health Check
echo "1. Testing Health Check..."
curl -s -X GET "$BASE_URL/health" | jq .
echo ""

# Test 2: User Registration
echo "2. Testing User Registration..."
SIGNUP_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@xara.com",
    "username": "testuser",
    "full_name": "Test User",
    "password": "testpass123"
  }')
echo $SIGNUP_RESPONSE | jq .
echo ""

# Test 3: User Login
echo "3. Testing User Login..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@xara.com",
    "password": "testpass123"
  }')
TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
echo "Token: $TOKEN"
echo ""

# Test 4: Screen Registration
echo "4. Testing Screen Registration..."
curl -s -X POST "$BASE_URL/screens/register" \
  -H "Content-Type: application/json" \
  -d '{
    "screen_id": "SCREEN_001",
    "name": "Mall Entrance",
    "location": "Dubai Mall",
    "resolution": "1920x1080"
  }' | jq .
echo ""

# Test 5: Get All Screens
echo "5. Testing Get All Screens..."
curl -s -X GET "$BASE_URL/screens/" | jq .
echo ""

# Test 6: Create Campaign
echo "6. Testing Campaign Creation..."
CAMPAIGN_RESPONSE=$(curl -s -X POST "$BASE_URL/campaigns/" \
  -H "Authorization: Bearer $TOKEN" \
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
  }')
CAMPAIGN_ID=$(echo $CAMPAIGN_RESPONSE | jq -r '._id // .id')
echo $CAMPAIGN_RESPONSE | jq .
echo ""

# Test 7: Get Current Campaign for Screen
echo "7. Testing Get Current Campaign for Screen..."
curl -s -X GET "$BASE_URL/playback/SCREEN_001/current-campaign" | jq .
echo ""

# Test 8: Record AI Metadata
echo "8. Testing AI Metadata Recording..."
curl -s -X POST "$BASE_URL/ai/metadata" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "SCREEN_001",
    "screen_id": "SCREEN_001",
    "emotion": "happy",
    "age_group": "18-25",
    "audience_count": 5,
    "engagement_score": 82,
    "detected_objects": ["person", "phone"]
  }' | jq .
echo ""

# Test 9: Record Analytics
echo "9. Testing Analytics Recording..."
curl -s -X POST "$BASE_URL/analytics/" \
  -H "Content-Type: application/json" \
  -d '{
    "screen_id": "SCREEN_001",
    "campaign_id": "'$CAMPAIGN_ID'",
    "play_count": 1,
    "impressions": 5,
    "engagement_score": 82,
    "audience_count": 5,
    "duration_watched": 30
  }' | jq .
echo ""

# Test 10: Get Screen Analytics
echo "10. Testing Get Screen Analytics..."
curl -s -X GET "$BASE_URL/analytics/screen/SCREEN_001" | jq .
echo ""

echo "=========================================="
echo "Testing Complete!"
echo "=========================================="
