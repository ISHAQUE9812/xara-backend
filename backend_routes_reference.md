# XARA Smart Signage: API Routes Reference Manual

Welcome to the central API routing documentation for the XARA Smart Signage Platform backend. This reference guide provides a complete, structured mapping of all active HTTP, WebSocket, and auxiliary endpoints, detailing their paths, source modules, authentication schemes, role restrictions, and operational descriptions.

> [!NOTE]
> All relative file paths are referenced from the backend repository root (`d:\Ishaque\xara-backend`).
> The backend runs on **FastAPI** (port `8000` locally) and is backed by **MongoDB**.

---

## 🔍 Swagger vs. Source Code Routing Audit

An exhaustive audit was conducted comparing the live endpoints registered in the FastAPI app instance (visible in Swagger UI at `/docs`) with the physical Python files in the `app` directory. 

### 1. Active & Registered Routes (Swagger UI `/docs`)
These routes are fully registered in `app/main.py` and are operational in the system:
* **Authentication (`/auth/*`)** - Served by `app/routes/auth.py`
* **Media & Advertisements (`/media/*` and `/ads/*`)** - Dual-registered prefix endpoints mapping to `app/ads/routes.py` for legacy compatibility
* **Campaigns (`/campaigns/*`)** - Served by `app/campaigns/routes.py`
* **Signage Screens (`/screens/*`)** - Served by `app/screens/routes.py`
* **WebSockets (`/ws/*`)** - Served by `app/websocket/screen_socket.py`
* **Analytics (`/analytics/*`)** - Served by `app/routes/analytics_routes.py`
* **User Management (`/users/*`)** - Served by `app/routes/user_routes.py`
* **Global Auxiliaries (`/reports`, `/health`, `/`)** - Defined directly in `app/main.py`

### 2. Unregistered, Legacy & Dead Code Files (Source Code Only)
These physical files exist in the codebase but are **NOT** imported or registered in `app/main.py`. Consequently, they do **not** appear in Swagger UI and cannot be reached:
* ⚠️ **`app/routes/auth_routes.py`**: Leftover legacy authentication file. It has been completely replaced by `app/routes/auth.py`. Contains unregistered endpoints `/register`, `/signup`, `/login`, and `/me`.
* ⚠️ **`app/routes/campaign_routes.py`**: Legacy campaign router. Completely replaced by `app/campaigns/routes.py` under the modular architecture.
* ⚠️ **`app/routes/screen_routes.py`**: Legacy screens router. Replaced entirely by `app/screens/routes.py`.
* ⚠️ **`app/routes/playback_routes.py`**: Legacy playback control endpoints (`/{screen_id}/current-campaign`, `/{screen_id}/trigger`, etc.). Playback is now managed programmatically by the background `playback_engine.py` and real-time WebSockets, making these endpoints obsolete.
* ⚠️ **`app/routes/ai_routes.py`**: Unregistered AI Decision Engine router (`/metadata`, `/decide/{screen_id}`, etc.). The current smart selection is handled asynchronously upon connection and loop rotations.

### 3. Duplicate Route Registrations (Dual Compatibility)
* 💡 **Media & Ads Shadow Routing**: The router `app/ads/routes.py` is registered twice in `app/main.py`:
  1. Once at prefix `/media`
  2. Once at prefix `/ads`
  This was an intentional architectural decision to support both modern and legacy frontend clients. Legacy uploads targeting `POST /media/upload` and `GET /media` resolve correctly, while new clients calling `POST /ads/upload` and `GET /ads` hit the same underlying services.

---

## 📋 Comprehensive API Route Directory

Below is the complete tabular reference of all registered endpoints in the XARA Backend application:

| HTTP Method | API Endpoint | Source File | Function Name | Auth Required | Admin Only | Description |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| **POST** | `/auth/signup` | `app/routes/auth.py` | `signup` | No | No | Register a new advertiser/user account (default role: `user`). |
| **POST** | `/auth/login` | `app/routes/auth.py` | `login` | No | No | Authenticate user credentials and return a signed JWT token and profile details. |
| **GET** | `/auth/me` | `app/routes/auth.py` | `read_current_user` | **Yes** | No | Retrieve the currently logged-in user's profile details. |
| **GET** | `/auth/admin/dashboard` | `app/routes/auth.py` | `admin_dashboard` | **Yes** | **Yes** | Authorized dashboard gateway welcome for administrators. |
| **GET** | `/auth/user/dashboard` | `app/routes/auth.py` | `user_dashboard` | **Yes** | No | Authorized dashboard gateway welcome for standard advertisers. |
| **POST** | `/media` | `app/ads/routes.py` | `upload_ad` | **Yes** | No | Upload a new advertisement asset and save it under the `ads` collection (alias). |
| **POST** | `/media/upload` | `app/ads/routes.py` | `upload_ad` | **Yes** | No | Legacy endpoint to upload an advertisement asset (compatibility mapping). |
| **GET** | `/media` | `app/ads/routes.py` | `get_all_ads` | **Yes** | No | Retrieve all ads (filtered by logged-in user for non-admins). |
| **GET** | `/media/my-ads` | `app/ads/routes.py` | `get_my_ads` | **Yes** | No | Retrieve all advertisements uploaded specifically by the current user. |
| **GET** | `/media/{ad_id}` | `app/ads/routes.py` | `get_ad_details` | **Yes** | No | Retrieve specific metadata details for a single advertisement. |
| **DELETE** | `/media/{ad_id}` | `app/ads/routes.py` | `delete_ad` | **Yes** | No | Permanently delete an advertisement metadata record and its asset file. |
| **POST** | `/ads` | `app/ads/routes.py` | `upload_ad` | **Yes** | No | Upload a new advertisement asset and save it under the `ads` collection. |
| **POST** | `/ads/upload` | `app/ads/routes.py` | `upload_ad` | **Yes** | No | Upload a new advertisement asset (standard path). |
| **GET** | `/ads` | `app/ads/routes.py` | `get_all_ads` | **Yes** | No | Retrieve all active advertisements in the system. |
| **GET** | `/ads/my-ads` | `app/ads/routes.py` | `get_my_ads` | **Yes** | No | Retrieve all active advertisements uploaded specifically by the current user. |
| **GET** | `/ads/{ad_id}` | `app/ads/routes.py` | `get_ad_details` | **Yes** | No | Retrieve specific metadata details for a single advertisement. |
| **DELETE** | `/ads/{ad_id}` | `app/ads/routes.py` | `delete_ad` | **Yes** | No | Permanently delete an advertisement metadata record and its asset file. |
| **POST** | `/campaigns` | `app/campaigns/routes.py` | `create_campaign` | **Yes** | No | Create a new advertising campaign grouping multiple advertisements. |
| **GET** | `/campaigns` | `app/campaigns/routes.py` | `get_campaigns` | **Yes** | No | Retrieve active campaigns (filters to own campaigns for non-admins). |
| **GET** | `/campaigns/{campaign_id}` | `app/campaigns/routes.py` | `get_campaign_details` | **Yes** | No | Retrieve details for a single campaign (validates user ownership). |
| **PATCH** | `/campaigns/{campaign_id}` | `app/campaigns/routes.py` | `update_campaign` | **Yes** | No | Modify properties or associated ad IDs of a campaign (partially). |
| **PUT** | `/campaigns/{campaign_id}` | `app/campaigns/routes.py` | `update_campaign` | **Yes** | No | Modify properties or associated ad IDs of a campaign (completely). |
| **DELETE** | `/campaigns/{campaign_id}` | `app/campaigns/routes.py` | `delete_campaign` | **Yes** | No | Permanently delete a campaign. |
| **POST** | `/screens` | `app/screens/routes.py` | `create_screen` | **Yes** | **Yes** | Register a new smart screen node in the database. |
| **POST** | `/screens/create` | `app/screens/routes.py` | `create_screen` | **Yes** | **Yes** | Register a new smart screen node in the database (standard path). |
| **GET** | `/screens` | `app/screens/routes.py` | `get_screens` | **Yes** | No | List registered digital signage display screens in the system. |
| **GET** | `/screens/live` | `app/screens/routes.py` | `get_live_monitoring` | **Yes** | **Yes** | Retrieve all currently online display screens with active playback telemetry. |
| **GET** | `/screens/{screen_id}` | `app/screens/routes.py` | `get_screen_by_id` | **Yes** | No | Fetch detailed metadata configuration for a single screen. |
| **PUT** | `/screens/{screen_id}` | `app/screens/routes.py` | `update_screen` | **Yes** | **Yes** | Update a screen's name, resolution, or hardware properties. |
| **DELETE** | `/screens/{screen_id}` | `app/screens/routes.py` | `delete_screen` | **Yes** | **Yes** | Permanently delete a screen node and clear its playlist mappings. |
| **POST** | `/screens/assign-ad` | `app/screens/routes.py` | `assign_ad` | **Yes** | **Yes** | Assign a single advertisement to a screen (forces Single mode playback). |
| **GET** | `/screens/{screen_id}/current-media` | `app/screens/routes.py` | `get_current_media` | No | No | Public endpoint for smart screens to fetch their active assigned play assets. |
| **WS** | `/ws/{screen_id}` | `app/websocket/screen_socket.py` | `screen_websocket` | **Yes** | No | Real-time screen sync connection for heartbeats, status updates, and interrupts. |
| **POST** | `/analytics` | `app/routes/analytics_routes.py` | `record_analytics` | **Yes** | No | Log a new playback analytics heartbeat (audience, engagement, plays). |
| **GET** | `/analytics` | `app/routes/analytics_routes.py` | `get_user_analytics` | **Yes** | No | Retrieve historical analytics log lists (filtered by user context). |
| **GET** | `/analytics/reports` | `app/routes/analytics_routes.py` | `get_user_reports` | **Yes** | No | Generate summary reach reports for advertiser campaign dashboards. |
| **GET** | `/analytics/global` | `app/routes/analytics_routes.py` | `get_global_analytics` | **Yes** | **Yes** | Aggregate platform-wide viewer telemetry across all screens (Admin only). |
| **GET** | `/analytics/screens` | `app/routes/analytics_routes.py` | `get_screens_analytics` | **Yes** | **Yes** | Retrieve performance and utilization analytics per screen node (Admin only). |
| **GET** | `/analytics/users` | `app/routes/analytics_routes.py` | `get_users_analytics` | **Yes** | **Yes** | Retrieve performance and billing analytics per advertiser user (Admin only). |
| **GET** | `/users` | `app/routes/user_routes.py` | `get_all_users` | **Yes** | **Yes** | View the list of all registered users in the database (Admin only). |
| **PATCH** | `/users/{user_id}/activate` | `app/routes/user_routes.py` | `activate_user` | **Yes** | **Yes** | Re-enable a suspended user account (Admin only). |
| **PATCH** | `/users/{user_id}/deactivate` | `app/routes/user_routes.py` | `deactivate_user` | **Yes** | **Yes** | Terminate sessions and block access for a user (Admin only). |
| **DELETE** | `/users/{user_id}` | `app/routes/user_routes.py` | `delete_user` | **Yes** | **Yes** | Permanently erase a user account and profiles (Admin only). |
| **GET** | `/reports` | `app/main.py` | `get_reports_api` | **Yes** | No | Pipeline aggregation analytics query endpoint for advertiser campaign summaries. |
| **GET** | `/health` | `app/main.py` | `health_check` | No | No | System health check returning uptime and socket connection stats. |
| **GET** | `/` | `app/main.py` | `root` | No | No | Gateway API index welcome endpoint. |
