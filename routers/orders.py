"""
Orders router for DoorDash-like food delivery app.

Endpoints:
  POST  /api/orders                         — create order from cart
  GET   /api/orders/{user_id}               — list all orders for user (newest first)
  GET   /api/orders/{user_id}/{order_id}    — get single order
  PUT   /api/orders/{order_id}/status       — update order status
"""
import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, HTTPException

from doordash_app.models import OrderCreateRequest, OrderStatusUpdate, carts_db, orders_db, restaurants_db

router = APIRouter(prefix="/api/orders", tags=["orders"])

# Valid status transitions: each key may only move to the values listed
VALID_TRANSITIONS: dict = {
    "confirmed": ["preparing"],
    "preparing": ["out_for_delivery"],
    "out_for_delivery": ["delivered"],
    "delivered": [],
}


# ---------------------------------------------------------------------------
# POST /api/orders
# ---------------------------------------------------------------------------

@router.post("", summary="Place an order", status_code=201)
def create_order(body: OrderCreateRequest) -> dict:
    """
    Place an order from the user's current cart.

    - Returns 400 if the cart is empty or doesn't exist.
    - Creates an order with status "confirmed".
    - Clears the user's cart after a successful order.
    """
    user_id: str = body.user_id
    delivery_address: str = body.delivery_address

    cart = carts_db.get(user_id)
    if cart is None or not cart.get("items"):
        raise HTTPException(
            status_code=400,
            detail="Cannot place order: cart is empty or does not exist.",
        )

    restaurant_id: str = cart["restaurant_id"]
    restaurant = restaurants_db.get(restaurant_id, {})

    now = datetime.now(timezone.utc).isoformat()
    order_id = str(uuid.uuid4())

    order: dict = {
        "order_id": order_id,
        "user_id": user_id,
        "restaurant_id": restaurant_id,
        "restaurant_name": restaurant.get("name", "Unknown Restaurant"),
        "items": [dict(item) for item in cart["items"]],  # deep copy of items
        "subtotal": cart["subtotal"],
        "delivery_fee": cart["delivery_fee"],
        "tax": cart["tax"],
        "total": cart["total"],
        "delivery_address": delivery_address,
        "status": "confirmed",
        "created_at": now,
        "updated_at": now,
    }

    # Persist order
    if user_id not in orders_db:
        orders_db[user_id] = []
    orders_db[user_id].append(order)

    # Clear cart after successful order
    carts_db[user_id] = {
        "user_id": user_id,
        "restaurant_id": None,
        "items": [],
        "subtotal": 0.0,
        "delivery_fee": 0.0,
        "tax": 0.0,
        "total": 0.0,
    }

    return order


# ---------------------------------------------------------------------------
# GET /api/orders/{user_id}
# ---------------------------------------------------------------------------

@router.get("/{user_id}", summary="List orders for a user")
def list_orders(user_id: str) -> List[dict]:
    """Return all orders for the user sorted newest-first (by created_at)."""
    user_orders = orders_db.get(user_id, [])
    return sorted(user_orders, key=lambda o: o["created_at"], reverse=True)


# ---------------------------------------------------------------------------
# GET /api/orders/{user_id}/{order_id}
# ---------------------------------------------------------------------------

@router.get("/{user_id}/{order_id}", summary="Get a single order")
def get_order(user_id: str, order_id: str) -> dict:
    """Return a specific order by user_id and order_id. Returns 404 if not found."""
    user_orders = orders_db.get(user_id, [])
    for order in user_orders:
        if order["order_id"] == order_id:
            return order
    raise HTTPException(
        status_code=404,
        detail=f"Order '{order_id}' not found for user '{user_id}'.",
    )


# ---------------------------------------------------------------------------
# PUT /api/orders/{order_id}/status
# ---------------------------------------------------------------------------

@router.put("/{order_id}/status", summary="Update order status")
def update_order_status(order_id: str, body: OrderStatusUpdate) -> dict:
    """
    Update the status of an order.

    Allowed transitions:
      confirmed → preparing → out_for_delivery → delivered

    Returns 400 for invalid transitions, 404 if order not found.
    """
    new_status: str = body.status

    # Validate the requested status is a known state
    all_known_statuses = set(VALID_TRANSITIONS.keys()) | {
        s for targets in VALID_TRANSITIONS.values() for s in targets
    }
    if new_status not in all_known_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown status '{new_status}'. Valid statuses: {sorted(all_known_statuses)}.",
        )

    # Search all users' orders for the order_id
    for user_id, user_orders in orders_db.items():
        for order in user_orders:
            if order["order_id"] == order_id:
                current_status = order["status"]
                allowed_next = VALID_TRANSITIONS.get(current_status, [])
                if new_status not in allowed_next:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            f"Invalid status transition: '{current_status}' → '{new_status}'. "
                            f"Allowed next statuses: {allowed_next}."
                        ),
                    )
                order["status"] = new_status
                order["updated_at"] = datetime.now(timezone.utc).isoformat()
                return order

    raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found.")
