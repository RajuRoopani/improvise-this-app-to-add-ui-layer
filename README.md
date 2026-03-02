# DoorDash Food Delivery App

A full-stack food delivery web application built with **FastAPI**, **vanilla JavaScript**, and in-memory storage. Browse restaurants, filter by cuisine, search by name, manage your cart, place orders, and track order status in real-time.

## Features

✅ **Restaurant Discovery**
- Browse all available restaurants
- Filter by cuisine type (Pizza, Chinese, Mexican, Sushi, Indian, American, Thai, Italian)
- Search restaurants by name

✅ **Menu & Cart Management**
- View full menu for each restaurant
- Add items to cart with quantity control
- Update item quantities
- Remove individual items
- Clear entire cart
- Real-time totals: subtotal, tax (8%), delivery fee, and total

✅ **Order Management**
- Place orders from your cart
- Track order status (confirmed → preparing → out_for_delivery → delivered)
- View order history (newest first)
- View individual order details

✅ **User System**
- Demo user (`user1`) pre-configured
- Cart and order history tied to user ID

## Tech Stack

- **Backend**: FastAPI 0.104+
- **Frontend**: Vanilla JavaScript ES6, HTML5, CSS3
- **Data Storage**: In-memory dictionaries (no database)
- **Validation**: Pydantic v2
- **Testing**: pytest, pytest-asyncio, httpx
- **Server**: Uvicorn (ASGI)
- **CORS**: Enabled for demo (production should restrict origins)

## Project Structure

```
doordash_app/
├── main.py                    # FastAPI app, CORS, routers, static files, health check
├── models.py                  # In-memory storage dicts, Pydantic schemas, seed data
├── requirements.txt           # Dependencies
├── routers/
│   ├── __init__.py
│   ├── restaurants.py         # GET /api/restaurants, /api/restaurants/{id}
│   ├── menu.py                # GET /api/restaurants/{id}/menu
│   ├── cart.py                # Cart management (add, update, remove, clear)
│   ├── orders.py              # Orders (create, list, get, update status)
│   └── users.py               # Users (minimal stub with demo user)
├── static/
│   ├── index.html             # Frontend SPA HTML
│   ├── style.css              # Styling
│   └── app.js                 # JavaScript SPA logic (when available)
├── tests/
│   ├── __init__.py
│   ├── test_restaurants_menu.py  # Restaurant & menu endpoint tests
│   └── test_cart_orders.py       # Cart & orders endpoint tests
└── __init__.py
```

## Setup & Installation

### 1. Install Dependencies

```bash
cd /workspace
pip install -r doordash_app/requirements.txt
```

### 2. Run the Server

```bash
cd /workspace
uvicorn doordash_app.main:app --reload
```

Server starts at `http://localhost:8000`

### 3. Open in Browser

Navigate to **http://localhost:8000** to access the frontend SPA.

## API Endpoints

All endpoints use JSON request/response bodies. Base URL: `http://localhost:8000/api`

### Restaurants

**GET** `/api/restaurants`  
List all restaurants with optional filters.

Query parameters:
- `cuisine` (optional): Filter by cuisine type (case-insensitive) — e.g., `?cuisine=Pizza`
- `search` (optional): Filter by partial restaurant name (case-insensitive) — e.g., `?search=dragon`

Response:
```json
[
  {
    "id": "pizza-palace",
    "name": "Pizza Palace",
    "cuisine_type": "Pizza",
    "rating": 4.5,
    "delivery_time": "25-35 min",
    "delivery_fee": 2.99,
    "image_url": "https://picsum.photos/seed/pizza-palace/400/300",
    "address": "123 Main St, San Francisco, CA 94105",
    "description": "Award-winning New York-style pies baked fresh in our wood-fired oven."
  },
  ...
]
```

**GET** `/api/restaurants/{restaurant_id}`  
Get a single restaurant by ID.

Response:
```json
{
  "id": "pizza-palace",
  "name": "Pizza Palace",
  "cuisine_type": "Pizza",
  "rating": 4.5,
  "delivery_time": "25-35 min",
  "delivery_fee": 2.99,
  "image_url": "https://picsum.photos/seed/pizza-palace/400/300",
  "address": "123 Main St, San Francisco, CA 94105",
  "description": "Award-winning New York-style pies baked fresh in our wood-fired oven."
}
```

### Menu

**GET** `/api/restaurants/{restaurant_id}/menu`  
Get all menu items for a restaurant.

Response:
```json
[
  {
    "id": "pp-001",
    "restaurant_id": "pizza-palace",
    "name": "Margherita Pizza",
    "description": "San Marzano tomatoes, fresh mozzarella, fragrant basil.",
    "price": 14.99,
    "category": "Mains",
    "image_url": "https://picsum.photos/seed/margherita/300/200"
  },
  ...
]
```

### Cart

**POST** `/api/cart/add`  
Add an item to the user's cart.

Request body:
```json
{
  "user_id": "user1",
  "menu_item_id": "pp-001",
  "quantity": 2
}
```

Response: Returns updated cart with totals.
```json
{
  "user_id": "user1",
  "restaurant_id": "pizza-palace",
  "items": [
    {
      "menu_item_id": "pp-001",
      "name": "Margherita Pizza",
      "price": 14.99,
      "quantity": 2,
      "item_total": 29.98
    }
  ],
  "subtotal": 29.98,
  "delivery_fee": 2.99,
  "tax": 2.40,
  "total": 35.37
}
```

**GET** `/api/cart/{user_id}`  
Get the user's current cart.

Response: Same cart structure as above (empty cart if none exists).

**PUT** `/api/cart/{user_id}/items/{menu_item_id}`  
Update the quantity of an item in the cart.

Request body:
```json
{
  "quantity": 3
}
```

Response: Updated cart. Set `quantity` to 0 or less to remove the item.

**DELETE** `/api/cart/{user_id}/items/{menu_item_id}`  
Remove a specific item from the cart.

Response: Updated cart (item removed).

**DELETE** `/api/cart/{user_id}`  
Clear all items from the user's cart.

Response: Empty cart structure.

### Orders

**POST** `/api/orders`  
Place an order from the user's cart. Clears the cart on success.

Request body:
```json
{
  "user_id": "user1",
  "delivery_address": "456 Oak Ave, San Francisco, CA 94109"
}
```

Response: (status 201)
```json
{
  "order_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user1",
  "restaurant_id": "pizza-palace",
  "restaurant_name": "Pizza Palace",
  "items": [
    {
      "menu_item_id": "pp-001",
      "name": "Margherita Pizza",
      "price": 14.99,
      "quantity": 2,
      "item_total": 29.98
    }
  ],
  "subtotal": 29.98,
  "delivery_fee": 2.99,
  "tax": 2.40,
  "total": 35.37,
  "delivery_address": "456 Oak Ave, San Francisco, CA 94109",
  "status": "confirmed",
  "created_at": "2024-01-15T10:30:45.123456+00:00",
  "updated_at": "2024-01-15T10:30:45.123456+00:00"
}
```

**GET** `/api/orders/{user_id}`  
Get all orders for a user, sorted newest-first.

Response:
```json
[
  {
    "order_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "user1",
    ...order details...
  },
  ...
]
```

**GET** `/api/orders/{user_id}/{order_id}`  
Get a specific order.

Response: Single order object (same structure as POST response).

**PUT** `/api/orders/{order_id}/status`  
Update an order's status.

Valid transitions:
- `confirmed` → `preparing`
- `preparing` → `out_for_delivery`
- `out_for_delivery` → `delivered`
- `delivered` → (no further changes)

Request body:
```json
{
  "status": "preparing"
}
```

Response: Updated order object.

### Users

**GET** `/api/users`  
List available users (demo only has `user1`).

Response:
```json
{
  "users": [
    {
      "user_id": "user1",
      "name": "Demo User",
      "email": "demo@example.com"
    }
  ]
}
```

**GET** `/api/users/{user_id}`  
Get user details (only `user1` is seeded).

Response:
```json
{
  "user_id": "user1",
  "name": "Demo User",
  "email": "demo@example.com"
}
```

### Health Check

**GET** `/api/health`  
Confirm the API is running.

Response:
```json
{
  "status": "ok",
  "service": "DoorDash Food Delivery API"
}
```

## Seed Data

The app ships with **8 restaurants** pre-loaded with menus:

1. **Pizza Palace** (Pizza)
   - Rating: 4.5 ⭐
   - Delivery: 25-35 min | Fee: $2.99
   - 7 menu items (pizza, appetizers, desserts, drinks)

2. **Dragon Wok** (Chinese)
   - Rating: 4.3 ⭐
   - Delivery: 30-45 min | Fee: $1.99
   - 7 menu items (kung pao chicken, fried rice, dim sum, etc.)

3. **Taco Fiesta** (Mexican)
   - Rating: 4.6 ⭐
   - Delivery: 20-30 min | Fee: $0.99
   - 7 menu items (street tacos, burritos, quesadillas, etc.)

4. **Sakura Sushi** (Sushi)
   - Rating: 4.7 ⭐
   - Delivery: 35-50 min | Fee: $3.99
   - 7 menu items (rolls, nigiri, miso soup, mochi, etc.)

5. **Taj Mahal Kitchen** (Indian)
   - Rating: 4.4 ⭐
   - Delivery: 30-40 min | Fee: $2.49
   - 7 menu items (butter chicken, biryani, samosas, etc.)

6. **Burger Barn** (American)
   - Rating: 4.2 ⭐
   - Delivery: 20-30 min | Fee: $1.49
   - 7 menu items (smash burgers, fries, shakes, etc.)

7. **Thai Orchid** (Thai)
   - Rating: 4.5 ⭐
   - Delivery: 30-45 min | Fee: $2.99
   - 7 menu items (pad thai, curries, spring rolls, etc.)

8. **Bella Italia** (Italian)
   - Rating: 4.6 ⭐
   - Delivery: 25-40 min | Fee: $2.49
   - 7 menu items (pasta, risotto, tiramisu, etc.)

Total: **56 menu items** across all restaurants.

Seed data runs on import — the moment `models.py` is loaded, all restaurants and menu items are available to the API.

## Testing

Run all tests:
```bash
cd /workspace
python -m pytest doordash_app/tests/ -v
```

Run specific test file:
```bash
python -m pytest doordash_app/tests/test_restaurants_menu.py -v
python -m pytest doordash_app/tests/test_cart_orders.py -v
```

Run with coverage:
```bash
python -m pytest doordash_app/tests/ --cov=doordash_app --cov-report=term-missing
```

## Notes

- **In-memory storage**: All data is stored in Python dictionaries and is lost when the server restarts. Perfect for demo/development.
- **Single-restaurant carts**: Users can only add items from one restaurant to their cart. Adding items from a different restaurant clears the old cart.
- **Tax calculation**: 8% tax is applied to subtotal only (not delivery fee).
- **User ID**: Demo uses hardcoded `user1`. Frontend would need to implement real authentication for multiple users.
- **CORS**: Currently allows all origins (`*`). Restrict in production.
- **Import paths**: Routers use absolute imports (e.g., `from doordash_app.models import ...`).

## Example Workflow

1. **Start server**: `uvicorn doordash_app.main:app --reload`
2. **List restaurants**: `GET /api/restaurants`
3. **View menu**: `GET /api/restaurants/pizza-palace/menu`
4. **Add to cart**: `POST /api/cart/add` with `{"user_id": "user1", "menu_item_id": "pp-001", "quantity": 2}`
5. **Get cart**: `GET /api/cart/user1`
6. **Place order**: `POST /api/orders` with `{"user_id": "user1", "delivery_address": "..."}` (clears cart)
7. **Track order**: `GET /api/orders/user1/{order_id}`
8. **Update status**: `PUT /api/orders/{order_id}/status` with `{"status": "preparing"}`

## Architecture

See `/workspace/docs/doordash-architecture.md` for detailed design decisions, API contract, and data model.

---

Built by Team Claw 🐾
