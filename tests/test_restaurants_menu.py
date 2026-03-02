"""
Tests for models.py seed data, restaurants router, and menu router.
Uses a minimal FastAPI test app that registers only the routers owned by senior_dev_1.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from doordash_app.models import (
    restaurants_db,
    menu_items_db,
    carts_db,
    orders_db,
    CartAddRequest,
    CartUpdateRequest,
    OrderCreateRequest,
    OrderStatusUpdate,
    seed_data,
)
from doordash_app.routers import restaurants as restaurants_router
from doordash_app.routers import menu as menu_router

# ---------------------------------------------------------------------------
# Build a minimal test app with just the routers under test
# ---------------------------------------------------------------------------

app = FastAPI()
app.include_router(restaurants_router.router)
app.include_router(menu_router.router)

client = TestClient(app)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_db():
    """Ensure seed data is always present before each test."""
    restaurants_db.clear()
    menu_items_db.clear()
    carts_db.clear()
    orders_db.clear()
    seed_data()
    yield


# ---------------------------------------------------------------------------
# models.py — storage & seed data tests
# ---------------------------------------------------------------------------

class TestModels:
    def test_storage_dicts_exist(self):
        assert isinstance(restaurants_db, dict)
        assert isinstance(menu_items_db, dict)
        assert isinstance(carts_db, dict)
        assert isinstance(orders_db, dict)

    def test_seed_produces_8_restaurants(self):
        assert len(restaurants_db) == 8

    def test_all_restaurants_have_required_fields(self):
        required_fields = {"id", "name", "cuisine_type", "rating", "delivery_time",
                           "delivery_fee", "image_url", "address", "description"}
        for rid, r in restaurants_db.items():
            assert required_fields.issubset(r.keys()), f"Restaurant {rid} missing fields"

    def test_restaurant_field_types(self):
        for rid, r in restaurants_db.items():
            assert isinstance(r["id"], str), f"{rid}: id must be str"
            assert isinstance(r["name"], str), f"{rid}: name must be str"
            assert isinstance(r["rating"], float), f"{rid}: rating must be float"
            assert isinstance(r["delivery_fee"], float), f"{rid}: delivery_fee must be float"

    def test_every_restaurant_has_at_least_6_menu_items(self):
        for rid in restaurants_db:
            items = [i for i in menu_items_db.values() if i["restaurant_id"] == rid]
            assert len(items) >= 6, f"Restaurant {rid} has fewer than 6 menu items ({len(items)})"

    def test_every_restaurant_has_at_least_2_categories(self):
        for rid in restaurants_db:
            categories = {i["category"] for i in menu_items_db.values() if i["restaurant_id"] == rid}
            assert len(categories) >= 2, f"Restaurant {rid} has fewer than 2 categories ({categories})"

    def test_all_menu_items_have_required_fields(self):
        required_fields = {"id", "name", "description", "price", "category", "image_url", "restaurant_id"}
        for iid, item in menu_items_db.items():
            assert required_fields.issubset(item.keys()), f"Menu item {iid} missing fields"

    def test_menu_item_prices_are_positive_floats(self):
        for iid, item in menu_items_db.items():
            assert isinstance(item["price"], float), f"{iid}: price must be float"
            assert item["price"] > 0, f"{iid}: price must be positive"

    def test_menu_item_restaurant_ids_reference_valid_restaurants(self):
        for iid, item in menu_items_db.items():
            assert item["restaurant_id"] in restaurants_db, \
                f"Menu item {iid} references unknown restaurant_id {item['restaurant_id']}"

    # Pydantic schema smoke-tests
    def test_cart_add_request_schema(self):
        req = CartAddRequest(user_id="u1", menu_item_id="pp-001", quantity=2)
        assert req.user_id == "u1"
        assert req.menu_item_id == "pp-001"
        assert req.quantity == 2

    def test_cart_update_request_schema(self):
        req = CartUpdateRequest(quantity=5)
        assert req.quantity == 5

    def test_order_create_request_schema(self):
        req = OrderCreateRequest(user_id="u1", delivery_address="123 Main St")
        assert req.user_id == "u1"
        assert req.delivery_address == "123 Main St"

    def test_order_status_update_schema(self):
        req = OrderStatusUpdate(status="delivered")
        assert req.status == "delivered"


# ---------------------------------------------------------------------------
# GET /api/restaurants — list & filter tests
# ---------------------------------------------------------------------------

class TestListRestaurants:
    def test_returns_all_8_restaurants(self):
        resp = client.get("/api/restaurants")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 8

    def test_response_contains_required_fields(self):
        resp = client.get("/api/restaurants")
        assert resp.status_code == 200
        for r in resp.json():
            for field in ("id", "name", "cuisine_type", "rating", "delivery_time",
                          "delivery_fee", "image_url", "address", "description"):
                assert field in r, f"Missing field '{field}' in restaurant {r.get('id')}"

    def test_filter_by_cuisine_exact(self):
        resp = client.get("/api/restaurants?cuisine=Pizza")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == "pizza-palace"

    def test_filter_by_cuisine_case_insensitive(self):
        resp = client.get("/api/restaurants?cuisine=pizza")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["cuisine_type"] == "Pizza"

    def test_filter_by_cuisine_UPPERCASE(self):
        resp = client.get("/api/restaurants?cuisine=SUSHI")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == "sakura-sushi"

    def test_filter_by_nonexistent_cuisine_returns_empty(self):
        resp = client.get("/api/restaurants?cuisine=Greek")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_search_by_partial_name(self):
        resp = client.get("/api/restaurants?search=burger")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == "burger-barn"

    def test_search_case_insensitive(self):
        resp = client.get("/api/restaurants?search=DRAGON")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == "dragon-wok"

    def test_search_no_match_returns_empty(self):
        resp = client.get("/api/restaurants?search=zzznothere")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_combined_search_and_cuisine_filter(self):
        # search "bella" AND cuisine "Italian"
        resp = client.get("/api/restaurants?search=bella&cuisine=Italian")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == "bella-italia"

    def test_combined_no_match(self):
        # valid search but wrong cuisine
        resp = client.get("/api/restaurants?search=pizza&cuisine=Thai")
        assert resp.status_code == 200
        assert resp.json() == []


# ---------------------------------------------------------------------------
# GET /api/restaurants/{restaurant_id} — single restaurant tests
# ---------------------------------------------------------------------------

class TestGetRestaurant:
    def test_get_existing_restaurant(self):
        resp = client.get("/api/restaurants/pizza-palace")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "pizza-palace"
        assert data["name"] == "Pizza Palace"

    def test_get_all_named_restaurants(self):
        ids = [
            "pizza-palace", "dragon-wok", "taco-fiesta", "sakura-sushi",
            "taj-mahal-kitchen", "burger-barn", "thai-orchid", "bella-italia",
        ]
        for rid in ids:
            resp = client.get(f"/api/restaurants/{rid}")
            assert resp.status_code == 200, f"Expected 200 for {rid}, got {resp.status_code}"

    def test_get_nonexistent_restaurant_returns_404(self):
        resp = client.get("/api/restaurants/does-not-exist")
        assert resp.status_code == 404

    def test_404_detail_message(self):
        resp = client.get("/api/restaurants/ghost-restaurant")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Restaurant not found"

    def test_response_fields_match_spec(self):
        resp = client.get("/api/restaurants/burger-barn")
        assert resp.status_code == 200
        data = resp.json()
        assert data["cuisine_type"] == "American"
        assert data["rating"] == 4.2
        assert data["delivery_fee"] == 1.49


# ---------------------------------------------------------------------------
# GET /api/restaurants/{restaurant_id}/menu — menu tests
# ---------------------------------------------------------------------------

class TestGetMenu:
    def test_returns_items_for_existing_restaurant(self):
        resp = client.get("/api/restaurants/pizza-palace/menu")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 6

    def test_all_items_belong_to_requested_restaurant(self):
        resp = client.get("/api/restaurants/dragon-wok/menu")
        assert resp.status_code == 200
        for item in resp.json():
            assert item["restaurant_id"] == "dragon-wok"

    def test_menu_item_has_required_fields(self):
        resp = client.get("/api/restaurants/taco-fiesta/menu")
        assert resp.status_code == 200
        for item in resp.json():
            for field in ("id", "name", "description", "price", "category", "image_url", "restaurant_id"):
                assert field in item, f"Missing field '{field}' in item {item.get('id')}"

    def test_menu_covers_multiple_categories(self):
        resp = client.get("/api/restaurants/sakura-sushi/menu")
        assert resp.status_code == 200
        categories = {item["category"] for item in resp.json()}
        assert len(categories) >= 2

    def test_nonexistent_restaurant_returns_404(self):
        resp = client.get("/api/restaurants/ghost/menu")
        assert resp.status_code == 404

    def test_404_detail_message(self):
        resp = client.get("/api/restaurants/nothing-here/menu")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Restaurant not found"

    def test_all_restaurants_have_menus(self):
        ids = [
            "pizza-palace", "dragon-wok", "taco-fiesta", "sakura-sushi",
            "taj-mahal-kitchen", "burger-barn", "thai-orchid", "bella-italia",
        ]
        for rid in ids:
            resp = client.get(f"/api/restaurants/{rid}/menu")
            assert resp.status_code == 200, f"Menu 404 for {rid}"
            assert len(resp.json()) >= 6, f"Fewer than 6 items for {rid}"
