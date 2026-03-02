"""
Cart router for DoorDash-like food delivery app.

Endpoints:
  POST   /api/cart/add                        — add item to cart
  GET    /api/cart/{user_id}                  — get cart with totals
  PUT    /api/cart/{user_id}/items/{item_id}  — update quantity
  DELETE /api/cart/{user_id}/items/{item_id}  — remove item
  DELETE /api/cart/{user_id}                  — clear cart
"""
from typing import Any

from fastapi import APIRouter, HTTPException

from doordash_app.models import CartAddRequest, CartUpdateRequest, carts_db, menu_items_db, restaurants_db

router = APIRouter(prefix="/api/cart", tags=["cart"])

TAX_RATE = 0.08  # 8 % tax on subtotal


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _empty_cart(user_id: str) -> dict:
    return {
        "user_id": user_id,
        "restaurant_id": None,
        "items": [],
        "subtotal": 0.0,
        "delivery_fee": 0.0,
        "tax": 0.0,
        "total": 0.0,
    }


def _recalculate(cart: dict) -> dict:
    """Recompute subtotal, tax, delivery_fee, and total in-place and return the cart."""
    subtotal = sum(item["item_total"] for item in cart["items"])

    # delivery_fee comes from the restaurant record
    delivery_fee = 0.0
    if cart.get("restaurant_id") and cart["items"]:
        restaurant = restaurants_db.get(cart["restaurant_id"])
        if restaurant:
            delivery_fee = float(restaurant.get("delivery_fee", 0.0))

    tax = round(subtotal * TAX_RATE, 2)
    subtotal = round(subtotal, 2)
    total = round(subtotal + delivery_fee + tax, 2)

    cart["subtotal"] = subtotal
    cart["delivery_fee"] = delivery_fee
    cart["tax"] = tax
    cart["total"] = total
    return cart


# ---------------------------------------------------------------------------
# POST /api/cart/add
# ---------------------------------------------------------------------------

@router.post("/add", summary="Add item to cart")
def add_to_cart(body: CartAddRequest) -> dict:
    """
    Add a menu item to the user's cart.

    - Validates menu_item_id exists (404 if not).
    - Enforces single-restaurant rule: if existing cart has items from a
      different restaurant, the old cart is cleared first.
    - Updates quantity if the item is already in the cart.
    - Returns the updated cart with recalculated totals.
    """
    user_id: str = body.user_id
    menu_item_id: str = body.menu_item_id
    quantity: int = body.quantity

    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than 0.")

    menu_item = menu_items_db.get(menu_item_id)
    if menu_item is None:
        raise HTTPException(status_code=404, detail=f"Menu item '{menu_item_id}' not found.")

    item_restaurant_id: str = menu_item["restaurant_id"]

    cart = carts_db.get(user_id)
    if cart is None:
        cart = _empty_cart(user_id)

    # Enforce single-restaurant rule
    if cart["items"] and cart["restaurant_id"] != item_restaurant_id:
        cart = _empty_cart(user_id)

    cart["restaurant_id"] = item_restaurant_id

    # Update existing or insert new line item
    for existing in cart["items"]:
        if existing["menu_item_id"] == menu_item_id:
            existing["quantity"] += quantity
            existing["item_total"] = round(existing["price"] * existing["quantity"], 2)
            break
    else:
        price = float(menu_item["price"])
        cart["items"].append({
            "menu_item_id": menu_item_id,
            "name": menu_item["name"],
            "price": price,
            "quantity": quantity,
            "item_total": round(price * quantity, 2),
        })

    _recalculate(cart)
    carts_db[user_id] = cart
    return cart


# ---------------------------------------------------------------------------
# GET /api/cart/{user_id}
# ---------------------------------------------------------------------------

@router.get("/{user_id}", summary="Get user cart")
def get_cart(user_id: str) -> dict:
    """Return the user's cart with all calculated totals.
    Returns an empty cart structure if the user has no active cart."""
    cart = carts_db.get(user_id)
    if cart is None:
        return _empty_cart(user_id)
    return cart


# ---------------------------------------------------------------------------
# PUT /api/cart/{user_id}/items/{item_id}
# ---------------------------------------------------------------------------

@router.put("/{user_id}/items/{item_id}", summary="Update item quantity in cart")
def update_cart_item(user_id: str, item_id: str, body: CartUpdateRequest) -> dict:
    """
    Update the quantity of an item in the cart.

    - If quantity <= 0, the item is removed.
    - Recalculates totals after update.
    - Returns 404 if the item is not in the cart.
    """
    cart = carts_db.get(user_id)
    if cart is None or not cart["items"]:
        raise HTTPException(status_code=404, detail=f"Item '{item_id}' not found in cart.")

    for existing in cart["items"]:
        if existing["menu_item_id"] == item_id:
            if body.quantity <= 0:
                cart["items"].remove(existing)
            else:
                existing["quantity"] = body.quantity
                existing["item_total"] = round(existing["price"] * body.quantity, 2)
            # Clear restaurant if cart becomes empty
            if not cart["items"]:
                cart["restaurant_id"] = None
            _recalculate(cart)
            carts_db[user_id] = cart
            return cart

    raise HTTPException(status_code=404, detail=f"Item '{item_id}' not found in cart.")


# ---------------------------------------------------------------------------
# DELETE /api/cart/{user_id}/items/{item_id}
# ---------------------------------------------------------------------------

@router.delete("/{user_id}/items/{item_id}", summary="Remove item from cart")
def remove_cart_item(user_id: str, item_id: str) -> dict:
    """
    Remove a specific item from the cart.

    - Recalculates totals after removal.
    - Returns 404 if the item is not found.
    """
    cart = carts_db.get(user_id)
    if cart is None or not cart["items"]:
        raise HTTPException(status_code=404, detail=f"Item '{item_id}' not found in cart.")

    for existing in cart["items"]:
        if existing["menu_item_id"] == item_id:
            cart["items"].remove(existing)
            if not cart["items"]:
                cart["restaurant_id"] = None
            _recalculate(cart)
            carts_db[user_id] = cart
            return cart

    raise HTTPException(status_code=404, detail=f"Item '{item_id}' not found in cart.")


# ---------------------------------------------------------------------------
# DELETE /api/cart/{user_id}
# ---------------------------------------------------------------------------

@router.delete("/{user_id}", summary="Clear entire cart")
def clear_cart(user_id: str) -> dict:
    """Remove all items from the user's cart and return an empty cart."""
    carts_db[user_id] = _empty_cart(user_id)
    return carts_db[user_id]
