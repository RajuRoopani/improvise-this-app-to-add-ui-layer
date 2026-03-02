"""
Menu router — GET /api/restaurants/{restaurant_id}/menu
"""

from typing import List

from fastapi import APIRouter, HTTPException

from doordash_app.models import menu_items_db, restaurants_db

router = APIRouter(prefix="/api/restaurants", tags=["menu"])


@router.get("/{restaurant_id}/menu", response_model=List[dict])
def get_menu(restaurant_id: str) -> List[dict]:
    """Return all menu items for a restaurant. 404 if the restaurant doesn't exist."""
    if restaurant_id not in restaurants_db:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    items = [item for item in menu_items_db.values() if item["restaurant_id"] == restaurant_id]
    return items
