from datetime import datetime
from typing import Dict, Any

class UserModel:
    @staticmethod
    def create_document(user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare a user document for MongoDB insertion.
        Adds timestamps and ensures required fields are present.
        """
        now = datetime.utcnow()
        return {
            "name": user_data.get("name"),
            "email": user_data.get("email"),
            "hashed_password": user_data.get("hashed_password"),
            "role": user_data.get("role", "user"),
            "is_active": user_data.get("is_active", True),
            "created_at": now,
            "updated_at": now,
        }

    @staticmethod
    def format_response(user: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB user document to API response format.
        Removes internal fields like _id and hashed_password.
        """
        if not user:
            return {}
        user["id"] = str(user.pop("_id"))
        # Remove sensitive field
        user.pop("hashed_password", None)
        return user
