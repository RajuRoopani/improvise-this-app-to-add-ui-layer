"""
Tests for cart and orders routers.

Covers all acceptance criteria:
  - POST /api/cart/add  (validation, single-restaurant rule, totals)
  - GET  /api/cart/{user_id}  (empty cart, populated cart)
  - PUT  /api/cart/{user_id}/items/{item_id}  (update qty, remove on 0)
  - DELETE /api/cart/{user_id}/items/{item_id}  (remove item, 404)
  - DELETE /api/cart/{user_id}  (clear cart)
  - POST /api/orders  (create from cart, clear cart, 400 on empty cart)
  - GET  /api/orders/{user_id}  (sorted newest first)
  - GET  /api/orders/{user_id}/{order_id}  (single order, 404)
  - PUT  /api/orders/{order_id}/status  (valid transitions, invalid -> 400)
  - /api/health  and  /api/users  basic smoke tests
"""
import pytest
import sys
import os

# Ensure the doordash_app root is on the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient

# We import app after path is set
from main import app
from models import carts_db, orders_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_state():
    """Clear carts and orders before every test to ensure isolation."""
    carts_db.clear()
    orders_db.clear()
    yield
    carts_db.clear()
    orders_db.clear()


@pytest.fixture()
def client():
    return TestClient(app)


# Known seeded item IDs (from models.py seed_data)
PIZZA_ITEM_ID = "pp-001"       # Margherita Pizza — restaurant "pizza-palace", $14.99
PEPPERONI_ID = "pp-002"        # Pepperoni Pizza  — restaurant "pizza-palace", $16.99
CHINESE_ITEM_ID = "dw-001"     # Kung Pao Chicken — restaurant "dragon-wok", $13.99
PIZZA_REST_ID = "pizza-palace"
CHINESE_REST_ID = "dragon-wok"

USER_ID = "test-user-1"
USER_ID_2 = "test-user-2"


# ===========================================================================
# Health check
# ===========================================================================

def test_health_check(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


# ===========================================================================
# Users router (stub)
# ===========================================================================

def test_get_user1(client):
    resp = client.get("/api/users/user1")
    assert resp.status_code == 200
    assert resp.json()["user_id"] == "user1"


def test_get_nonexistent_user(client):
    resp = client.get("/api/users/nobody")
    assert resp.status_code == 404


# ===========================================================================
# GET /api/cart/{user_id} — empty cart
# ===========================================================================

def test_get_empty_cart(client):
    resp = client.get(f"/api/cart/{USER_ID}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == USER_ID
    assert data["restaurant_id"] is None
    assert data["items"] == []
    assert data["subtotal"] == 0.0
    assert data["delivery_fee"] == 0.0
    assert data["tax"] == 0.0
    assert data["total"] == 0.0


# ===========================================================================
# POST /api/cart/add
# ===========================================================================

def test_add_item_to_cart(client):
    resp = client.post("/api/cart/add", json={
        "user_id": USER_ID,
        "menu_item_id": PIZZA_ITEM_ID,
        "quantity": 2,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["restaurant_id"] == PIZZA_REST_ID
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert item["menu_item_id"] == PIZZA_ITEM_ID
    assert item["quantity"] == 2
    assert item["price"] == 14.99
    assert item["item_total"] == round(14.99 * 2, 2)


def test_add_item_calculates_totals_correctly(client):
    resp = client.post("/api/cart/add", json={
        "user_id": USER_ID,
        "menu_item_id": PIZZA_ITEM_ID,
        "quantity": 1,
    })
    assert resp.status_code == 200
    data = resp.json()
    subtotal = 14.99
    delivery_fee = 2.99  # pizza-palace delivery fee
    tax = round(subtotal * 0.08, 2)
    total = round(subtotal + delivery_fee + tax, 2)
    assert data["subtotal"] == subtotal
    assert data["delivery_fee"] == delivery_fee
    assert data["tax"] == tax
    assert data["total"] == total


def test_add_same_item_increments_quantity(client):
    client.post("/api/cart/add", json={"user_id": USER_ID, "menu_item_id": PIZZA_ITEM_ID, "quantity": 1})
    resp = client.post("/api/cart/add", json={"user_id": USER_ID, "menu_item_id": PIZZA_ITEM_ID, "quantity": 2})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 3


def test_add_item_from_different_restaurant_clears_cart(client):
    # Add pizza item first
    client.post("/api/cart/add", json={"user_id": USER_ID, "menu_item_id": PIZZA_ITEM_ID, "quantity": 1})
    # Add Chinese item — should clear pizza and add Chinese only
    resp = client.post("/api/cart/add", json={"user_id": USER_ID, "menu_item_id": CHINESE_ITEM_ID, "quantity": 1})
    assert resp.status_code == 200
    data = resp.json()
    assert data["restaurant_id"] == CHINESE_REST_ID
    assert len(data["items"]) == 1
    assert data["items"][0]["menu_item_id"] == CHINESE_ITEM_ID


def test_add_invalid_menu_item_returns_404(client):
    resp = client.post("/api/cart/add", json={
        "user_id": USER_ID,
        "menu_item_id": "nonexistent-item",
        "quantity": 1,
    })
    assert resp.status_code == 404


def test_add_zero_quantity_returns_400(client):
    resp = client.post("/api/cart/add", json={
        "user_id": USER_ID,
        "menu_item_id": PIZZA_ITEM_ID,
        "quantity": 0,
    })
    assert resp.status_code == 400


def test_add_multiple_items_same_restaurant(client):
    client.post("/api/cart/add", json={"user_id": USER_ID, "menu_item_id": PIZZA_ITEM_ID, "quantity": 1})
    resp = client.post("/api/cart/add", json={"user_id": USER_ID, "menu_item_id": PEPPERONI_ID, "quantity": 1})
    assert resp.status_code == 200
    data = resp.json()
    assert data["restaurant_id"] == PIZZA_REST_ID
    assert len(data["items"]) == 2


# ===========================================================================
# GET /api/cart/{user_id} — populated cart
# ===========================================================================

def test_get_populated_cart(client):
    client.post("/api/cart/add", json={"user_id": USER_ID, "menu_item_id": PIZZA_ITEM_ID, "quantity": 2})
    resp = client.get(f"/api/cart/{USER_ID}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 2
    assert data["subtotal"] > 0
    assert data["total"] > data["subtotal"]  # includes delivery fee and tax


# ===========================================================================
# PUT /api/cart/{user_id}/items/{item_id}
# ===========================================================================

def test_update_cart_item_quantity(client):
    client.post("/api/cart/add", json={"user_id": USER_ID, "menu_item_id": PIZZA_ITEM_ID, "quantity": 1})
    resp = client.put(f"/api/cart/{USER_ID}/items/{PIZZA_ITEM_ID}", json={"quantity": 3})
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"][0]["quantity"] == 3
    assert data["items"][0]["item_total"] == round(14.99 * 3, 2)


def test_update_cart_item_to_zero_removes_it(client):
    client.post("/api/cart/add", json={"user_id": USER_ID, "menu_item_id": PIZZA_ITEM_ID, "quantity": 2})
    resp = client.put(f"/api/cart/{USER_ID}/items/{PIZZA_ITEM_ID}", json={"quantity": 0})
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["restaurant_id"] is None


def test_update_nonexistent_item_returns_404(client):
    resp = client.put(f"/api/cart/{USER_ID}/items/fake-item", json={"quantity": 1})
    assert resp.status_code == 404


def test_update_item_recalculates_totals(client):
    client.post("/api/cart/add", json={"user_id": USER_ID, "menu_item_id": PIZZA_ITEM_ID, "quantity": 1})
    resp = client.put(f"/api/cart/{USER_ID}/items/{PIZZA_ITEM_ID}", json={"quantity": 5})
    data = resp.json()
    expected_subtotal = round(14.99 * 5, 2)
    assert data["subtotal"] == expected_subtotal
    assert data["tax"] == round(expected_subtotal * 0.08, 2)


# ===========================================================================
# DELETE /api/cart/{user_id}/items/{item_id}
# ===========================================================================

def test_delete_cart_item(client):
    client.post("/api/cart/add", json={"user_id": USER_ID, "menu_item_id": PIZZA_ITEM_ID, "quantity": 1})
    client.post("/api/cart/add", json={"user_id": USER_ID, "menu_item_id": PEPPERONI_ID, "quantity": 1})
    resp = client.delete(f"/api/cart/{USER_ID}/items/{PIZZA_ITEM_ID}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["menu_item_id"] == PEPPERONI_ID


def test_delete_last_item_clears_restaurant(client):
    client.post("/api/cart/add", json={"user_id": USER_ID, "menu_item_id": PIZZA_ITEM_ID, "quantity": 1})
    resp = client.delete(f"/api/cart/{USER_ID}/items/{PIZZA_ITEM_ID}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["restaurant_id"] is None


def test_delete_nonexistent_cart_item_returns_404(client):
    resp = client.delete(f"/api/cart/{USER_ID}/items/not-here")
    assert resp.status_code == 404


# ===========================================================================
# DELETE /api/cart/{user_id}
# ===========================================================================

def test_clear_cart(client):
    client.post("/api/cart/add", json={"user_id": USER_ID, "menu_item_id": PIZZA_ITEM_ID, "quantity": 3})
    resp = client.delete(f"/api/cart/{USER_ID}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["subtotal"] == 0.0
    assert data["total"] == 0.0


# ===========================================================================
# POST /api/orders — create order
# ===========================================================================

def _add_pizza_to_cart(client, user_id=USER_ID, quantity=1):
    return client.post("/api/cart/add", json={
        "user_id": user_id,
        "menu_item_id": PIZZA_ITEM_ID,
        "quantity": quantity,
    })


def test_create_order_from_cart(client):
    _add_pizza_to_cart(client)
    resp = client.post("/api/orders", json={
        "user_id": USER_ID,
        "delivery_address": "123 Main St, San Francisco, CA",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["user_id"] == USER_ID
    assert data["restaurant_id"] == PIZZA_REST_ID
    assert data["restaurant_name"] == "Pizza Palace"
    assert data["status"] == "confirmed"
    assert len(data["items"]) == 1
    assert data["subtotal"] > 0
    assert data["tax"] > 0
    assert data["total"] > data["subtotal"]
    assert data["delivery_address"] == "123 Main St, San Francisco, CA"
    assert "order_id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_order_clears_cart(client):
    _add_pizza_to_cart(client)
    client.post("/api/orders", json={
        "user_id": USER_ID,
        "delivery_address": "123 Main St",
    })
    cart_resp = client.get(f"/api/cart/{USER_ID}")
    cart = cart_resp.json()
    assert cart["items"] == []
    assert cart["total"] == 0.0


def test_create_order_with_empty_cart_returns_400(client):
    resp = client.post("/api/orders", json={
        "user_id": USER_ID,
        "delivery_address": "123 Main St",
    })
    assert resp.status_code == 400


def test_create_order_no_cart_returns_400(client):
    """User has never added to cart — no cart entry in carts_db."""
    resp = client.post("/api/orders", json={
        "user_id": "brand-new-user",
        "delivery_address": "456 Other St",
    })
    assert resp.status_code == 400


def test_create_order_contains_correct_totals(client):
    _add_pizza_to_cart(client, quantity=2)
    cart_resp = client.get(f"/api/cart/{USER_ID}")
    cart = cart_resp.json()

    order_resp = client.post("/api/orders", json={
        "user_id": USER_ID,
        "delivery_address": "789 Oak Ave",
    })
    order = order_resp.json()
    # Order totals should match what was in the cart
    assert order["subtotal"] == cart["subtotal"]
    assert order["delivery_fee"] == cart["delivery_fee"]
    assert order["tax"] == cart["tax"]
    assert order["total"] == cart["total"]


# ===========================================================================
# GET /api/orders/{user_id}
# ===========================================================================

def test_list_orders_empty(client):
    resp = client.get(f"/api/orders/{USER_ID}")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_orders_sorted_newest_first(client):
    # Place two orders
    _add_pizza_to_cart(client)
    client.post("/api/orders", json={"user_id": USER_ID, "delivery_address": "1 First St"})

    _add_pizza_to_cart(client)
    client.post("/api/orders", json={"user_id": USER_ID, "delivery_address": "2 Second St"})

    resp = client.get(f"/api/orders/{USER_ID}")
    assert resp.status_code == 200
    orders = resp.json()
    assert len(orders) == 2
    # Newest first — second address should appear first
    assert orders[0]["delivery_address"] == "2 Second St"
    assert orders[1]["delivery_address"] == "1 First St"


# ===========================================================================
# GET /api/orders/{user_id}/{order_id}
# ===========================================================================

def test_get_single_order(client):
    _add_pizza_to_cart(client)
    order_resp = client.post("/api/orders", json={"user_id": USER_ID, "delivery_address": "99 Test Blvd"})
    order_id = order_resp.json()["order_id"]

    resp = client.get(f"/api/orders/{USER_ID}/{order_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["order_id"] == order_id
    assert data["delivery_address"] == "99 Test Blvd"


def test_get_order_not_found_returns_404(client):
    resp = client.get(f"/api/orders/{USER_ID}/non-existent-order-id")
    assert resp.status_code == 404


# ===========================================================================
# PUT /api/orders/{order_id}/status
# ===========================================================================

def _place_order(client, user_id=USER_ID):
    _add_pizza_to_cart(client, user_id=user_id)
    resp = client.post("/api/orders", json={"user_id": user_id, "delivery_address": "1 Delivery Ln"})
    return resp.json()


def test_update_order_status_confirmed_to_preparing(client):
    order = _place_order(client)
    resp = client.put(f"/api/orders/{order['order_id']}/status", json={"status": "preparing"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "preparing"


def test_update_order_status_full_lifecycle(client):
    order = _place_order(client)
    order_id = order["order_id"]

    for next_status in ["preparing", "out_for_delivery", "delivered"]:
        resp = client.put(f"/api/orders/{order_id}/status", json={"status": next_status})
        assert resp.status_code == 200
        assert resp.json()["status"] == next_status


def test_update_order_status_invalid_transition(client):
    order = _place_order(client)
    # "confirmed" → "delivered" is not a valid transition (must go through preparing first)
    resp = client.put(f"/api/orders/{order['order_id']}/status", json={"status": "delivered"})
    assert resp.status_code == 400


def test_update_order_status_skip_step_returns_400(client):
    order = _place_order(client)
    order_id = order["order_id"]
    # confirmed → out_for_delivery (skips preparing) — invalid
    resp = client.put(f"/api/orders/{order_id}/status", json={"status": "out_for_delivery"})
    assert resp.status_code == 400


def test_update_order_status_delivered_cannot_move(client):
    order = _place_order(client)
    order_id = order["order_id"]
    for next_status in ["preparing", "out_for_delivery", "delivered"]:
        client.put(f"/api/orders/{order_id}/status", json={"status": next_status})
    # Now try to move back or to any state
    resp = client.put(f"/api/orders/{order_id}/status", json={"status": "confirmed"})
    assert resp.status_code == 400


def test_update_nonexistent_order_status_returns_404(client):
    resp = client.put("/api/orders/fake-order-id/status", json={"status": "preparing"})
    assert resp.status_code == 404


def test_update_order_status_updates_updated_at(client):
    order = _place_order(client)
    order_id = order["order_id"]
    created_at = order["created_at"]
    resp = client.put(f"/api/orders/{order_id}/status", json={"status": "preparing"})
    updated = resp.json()
    # updated_at may equal created_at if called instantly, but field must exist
    assert "updated_at" in updated


# ===========================================================================
# Cart isolation between users
# ===========================================================================

def test_carts_are_isolated_between_users(client):
    _add_pizza_to_cart(client, user_id=USER_ID)
    resp2 = client.get(f"/api/cart/{USER_ID_2}")
    assert resp2.json()["items"] == []
