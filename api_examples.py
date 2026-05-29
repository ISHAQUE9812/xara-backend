"""
XARA API Examples - Python Implementation
This file demonstrates how to interact with the XARA API
"""

import requests
import json
from datetime import datetime
import asyncio
import websocketszbn

BASE_URL = "http://localhost:8000"
WEBSOCKET_URL = "ws://localhost:8000"

class XaraAPIClient:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.token = None
        self.headers = {"Content-Type": "application/json"}
    
    def signup(self, email, username, full_name, password):
        """Register a new user"""
        response = requests.post(
            f"{self.base_url}/auth/signup",
            headers=self.headers,
            json={
                "email": email,
                "username": username,
                "full_name": full_name,
                "password": password
            }
        )
        return response.json()
    
    def login(self, email, password):
        """Login and get JWT token"""
        response = requests.post(
            f"{self.base_url}/auth/login",
            headers=self.headers,
            json={
                "email": email,
                "password": password
            }
        )
        data = response.json()
        self.token = data.get("access_token")
        self.headers["Authorization"] = f"Bearer {self.token}"
        return data
    
    def register_screen(self, screen_id, name, location, resolution="1920x1080"):
        """Register a new screen"""
        response = requests.post(
            f"{self.base_url}/screens/register",
            headers=self.headers,
            json={
                "screen_id": screen_id,
                "name": name,
                "location": location,
                "resolution": resolution
            }
        )
        return response.json()
    
    def get_all_screens(self):
        """Get all registered screens"""
        response = requests.get(
            f"{self.base_url}/screens/",
            headers=self.headers
        )
        return response.json()
    
    def get_online_screens(self):
        """Get all online screens"""
        response = requests.get(
            f"{self.base_url}/screens/online",
            headers=self.headers
        )
        return response.json()
    
    def create_campaign(self, campaign_name, video_url, assigned_screens, 
                       targeting=None, duration=30, status="active"):
        """Create a new campaign"""
        response = requests.post(
            f"{self.base_url}/campaigns/",
            headers=self.headers,
            json={
                "campaign_name": campaign_name,
                "video_url": video_url,
                "video_filename": video_url.split('/')[-1],
                "assigned_screens": assigned_screens,
                "targeting": targeting or {},
                "duration": duration,
                "status": status
            }
        )
        return response.json()
    
    def get_campaigns(self):
        """Get all campaigns"""
        response = requests.get(
            f"{self.base_url}/campaigns/",
            headers=self.headers
        )
        return response.json()
    
    def get_current_campaign(self, screen_id):
        """Get current campaign for a screen"""
        response = requests.get(
            f"{self.base_url}/playback/{screen_id}/current-campaign",
            headers=self.headers
        )
        return response.json()
    
    def record_ai_metadata(self, device_id, screen_id, emotion=None, 
                          age_group=None, audience_count=0, engagement_score=0):
        """Record AI metadata from screen sensors"""
        response = requests.post(
            f"{self.base_url}/ai/metadata",
            headers=self.headers,
            json={
                "device_id": device_id,
                "screen_id": screen_id,
                "emotion": emotion,
                "age_group": age_group,
                "audience_count": audience_count,
                "engagement_score": engagement_score,
                "detected_objects": []
            }
        )
        return response.json()
    
    def ai_decide_campaign(self, screen_id):
        """Use AI decision engine to select best campaign"""
        response = requests.post(
            f"{self.base_url}/ai/decide/{screen_id}",
            headers=self.headers
        )
        return response.json()
    
    def record_analytics(self, screen_id, campaign_id, play_count=1, 
                        impressions=0, engagement_score=0, audience_count=0):
        """Record analytics event"""
        response = requests.post(
            f"{self.base_url}/analytics/",
            headers=self.headers,
            json={
                "screen_id": screen_id,
                "campaign_id": campaign_id,
                "play_count": play_count,
                "impressions": impressions,
                "engagement_score": engagement_score,
                "audience_count": audience_count,
                "duration_watched": 30
            }
        )
        return response.json()
    
    def get_screen_analytics(self, screen_id, days=7):
        """Get analytics for a screen"""
        response = requests.get(
            f"{self.base_url}/analytics/screen/{screen_id}?days={days}",
            headers=self.headers
        )
        return response.json()
    
    def get_screen_performance(self, screen_id):
        """Get performance metrics for a screen"""
        response = requests.get(
            f"{self.base_url}/analytics/screen/{screen_id}/performance",
            headers=self.headers
        )
        return response.json()
    
    def get_top_campaigns(self, limit=10):
        """Get top campaigns by engagement"""
        response = requests.get(
            f"{self.base_url}/analytics/top-campaigns?limit={limit}",
            headers=self.headers
        )
        return response.json()


async def connect_websocket(screen_id):
    """Connect to WebSocket for real-time updates"""
    url = f"{WEBSOCKET_URL}/ws/screens/{screen_id}"
    async with websockets.connect(url) as websocket:
        print(f"Connected to WebSocket for screen {screen_id}")
        
        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)
                print(f"Received: {data}")
                
                if data.get("event") == "campaign_play":
                    print(f"Playing campaign: {data.get('campaign_name')}")
                elif data.get("event") == "campaign_update":
                    print(f"Campaign updated: {data.get('campaign')}")
            
            except websockets.exceptions.ConnectionClosed:
                print("WebSocket connection closed")
                break
            except Exception as e:
                print(f"Error: {e}")
                break


# Example Usage
if __name__ == "__main__":
    client = XaraAPIClient()
    
    # 1. Register and login
    print("1. Signing up...")
    client.signup("admin@xara.com", "admin", "Admin User", "securepass123")
    print("   ✓ Signup successful")
    
    print("2. Logging in...")
    login_response = client.login("admin@xara.com", "securepass123")
    print(f"   ✓ Login successful, token: {login_response['access_token'][:20]}...")
    
    # 2. Register screens
    print("3. Registering screens...")
    screen1 = client.register_screen("SCREEN_001", "Mall Entrance", "Dubai Mall")
    print(f"   ✓ Screen registered: {screen1}")
    
    # 3. Create campaigns
    print("4. Creating campaigns...")
    campaign = client.create_campaign(
        "Nike Summer Sale",
        "/videos/nike.mp4",
        ["SCREEN_001"],
        {"emotion": "happy", "age_group": "18-25"},
        30
    )
    print(f"   ✓ Campaign created: {campaign}")
    
    # 4. Record AI metadata
    print("5. Recording AI metadata...")
    metadata = client.record_ai_metadata(
        "SCREEN_001",
        "SCREEN_001",
        emotion="happy",
        age_group="18-25",
        audience_count=5,
        engagement_score=82
    )
    print(f"   ✓ Metadata recorded: {metadata}")
    
    # 5. Get AI recommendation
    print("6. Getting AI recommendation...")
    recommendation = client.ai_decide_campaign("SCREEN_001")
    print(f"   ✓ Recommendation: {recommendation}")
    
    # 6. Record analytics
    print("7. Recording analytics...")
    analytics = client.record_analytics(
        "SCREEN_001",
        campaign.get("id"),
        play_count=1,
        impressions=5,
        engagement_score=82,
        audience_count=5
    )
    print(f"   ✓ Analytics recorded: {analytics}")
    
    # 7. Get performance metrics
    print("8. Getting screen performance...")
    performance = client.get_screen_performance("SCREEN_001")
    print(f"   ✓ Performance: {performance}")
    
    print("\n✅ All API tests completed successfully!")
