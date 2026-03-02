"""
Restaurant router — GET /api/restaurants and GET /api/restaurants/{restaurant_id}
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from doordash_app.models import restaurants_db

router = APIRouter(prefix="/api/restaurants", tags=["restaurants"])


@router.get("", response_model=List[dict])
def list_restaurants(
    cuisine: Optional[str] = Query(default=None, description="Filter by cuisine type (case-insensitive)"),
    search: Optional[str] = Query(default=None, description="Partial name match (case-insensitive)"),
) -> List[dict]:
    """Return all restaurants, with optional filtering by cuisine and/or name search."""
    results = list(restaurants_db.values())

    if cuisine:
        cuisine_lower = cuisine.lower()
        results = [r for r in results if r["cuisine_type"].lower() == cuisine_lower]

    if search:
        search_lower = search.lower()
        results = [r for r in results if search_lower in r["name"].lower()]

    return results


@router.get("/{restaurant_id}", response_model=dict)
def get_restaurant(restaurant_id: str) -> dict:
    """Return a single restaurant by ID. 404 if not found."""
    restaurant = restaurants_db.get(restaurant_id)
    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant
