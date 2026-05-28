from datetime import timedelta
from typing import Optional

from app.auth.jwt_handler import create_access_token, decode_token
from app.auth.auth_dependency import get_current_user
