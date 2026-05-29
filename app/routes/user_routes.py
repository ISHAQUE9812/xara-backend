from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from bson import ObjectId
from app.database.db import get_db
from app.auth.role_middleware import require_admin

router = APIRouter()

@router.get("", response_model=List[dict])
@router.get("/", response_model=List[dict])
async def get_all_users(
    current_user: dict = Depends(require_admin),
    db=Depends(get_db)
):
    cursor = db["users"].find({})
    users = await cursor.to_list(length=1000)
    for u in users:
        u["id"] = str(u.pop("_id"))
        u.pop("hashed_password", None)
    return users

@router.patch("/{user_id}/activate")
async def activate_user(
    user_id: str,
    current_user: dict = Depends(require_admin),
    db=Depends(get_db)
):
    try:
        obj_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID")
        
    result = await db["users"].update_one(
        {"_id": obj_id},
        {"$set": {"is_active": True}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    return {"detail": "User activated successfully"}

@router.patch("/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    current_user: dict = Depends(require_admin),
    db=Depends(get_db)
):
    try:
        obj_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID")
        
    result = await db["users"].update_one(
        {"_id": obj_id},
        {"$set": {"is_active": False}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    return {"detail": "User deactivated successfully"}

@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(require_admin),
    db=Depends(get_db)
):
    try:
        obj_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID")
        
    result = await db["users"].delete_one({"_id": obj_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    return {"detail": "User deleted successfully"}
