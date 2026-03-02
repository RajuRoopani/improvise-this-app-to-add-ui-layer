"""
DoorDash-like food delivery app — in-memory data models, Pydantic schemas, and seed data.
This module is the single source of truth for all storage dicts used by every router.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# In-memory storage
# ---------------------------------------------------------------------------

restaurants_db: Dict[str, dict] = {}    # restaurant_id -> restaurant dict
menu_items_db: Dict[str, dict] = {}     # menu_item_id  -> menu item dict
carts_db: Dict[str, dict] = {}          # user_id       -> cart dict
orders_db: Dict[str, list] = {}         # user_id       -> list of order dicts

# ---------------------------------------------------------------------------
# Pydantic request/response schemas
# ---------------------------------------------------------------------------

class CartAddRequest(BaseModel):
    user_id: str
    menu_item_id: str
    quantity: int


class CartUpdateRequest(BaseModel):
    quantity: int


class OrderCreateRequest(BaseModel):
    user_id: str
    delivery_address: str


class OrderStatusUpdate(BaseModel):
    status: str


# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

def seed_data() -> None:
    """Populate restaurants_db and menu_items_db with realistic sample data."""

    _restaurants = [
        {
            "id": "pizza-palace",
            "name": "Pizza Palace",
            "cuisine_type": "Pizza",
            "rating": 4.5,
            "delivery_time": "25-35 min",
            "delivery_fee": 2.99,
            "image_url": "https://picsum.photos/seed/pizza-palace/400/300",
            "address": "123 Main St, San Francisco, CA 94105",
            "description": "Award-winning New York-style pies baked fresh in our wood-fired oven.",
        },
        {
            "id": "dragon-wok",
            "name": "Dragon Wok",
            "cuisine_type": "Chinese",
            "rating": 4.3,
            "delivery_time": "30-45 min",
            "delivery_fee": 1.99,
            "image_url": "https://picsum.photos/seed/dragon-wok/400/300",
            "address": "456 Chinatown Ave, San Francisco, CA 94133",
            "description": "Authentic Cantonese and Sichuan dishes cooked to order with fresh ingredients.",
        },
        {
            "id": "taco-fiesta",
            "name": "Taco Fiesta",
            "cuisine_type": "Mexican",
            "rating": 4.6,
            "delivery_time": "20-30 min",
            "delivery_fee": 0.99,
            "image_url": "https://picsum.photos/seed/taco-fiesta/400/300",
            "address": "789 Mission St, San Francisco, CA 94103",
            "description": "Street-style tacos, burritos, and quesadillas bursting with bold flavors.",
        },
        {
            "id": "sakura-sushi",
            "name": "Sakura Sushi",
            "cuisine_type": "Sushi",
            "rating": 4.7,
            "delivery_time": "35-50 min",
            "delivery_fee": 3.99,
            "image_url": "https://picsum.photos/seed/sakura-sushi/400/300",
            "address": "321 Japantown Blvd, San Francisco, CA 94115",
            "description": "Master chefs craft every roll with premium, sustainably sourced fish.",
        },
        {
            "id": "taj-mahal-kitchen",
            "name": "Taj Mahal Kitchen",
            "cuisine_type": "Indian",
            "rating": 4.4,
            "delivery_time": "30-40 min",
            "delivery_fee": 2.49,
            "image_url": "https://picsum.photos/seed/taj-mahal-kitchen/400/300",
            "address": "654 Curry Lane, San Francisco, CA 94109",
            "description": "Rich curries, tandoor-roasted meats, and freshly baked naan every day.",
        },
        {
            "id": "burger-barn",
            "name": "Burger Barn",
            "cuisine_type": "American",
            "rating": 4.2,
            "delivery_time": "20-30 min",
            "delivery_fee": 1.49,
            "image_url": "https://picsum.photos/seed/burger-barn/400/300",
            "address": "101 Fillmore St, San Francisco, CA 94117",
            "description": "Juicy smash burgers, crispy fries, and thick milkshakes since 1987.",
        },
        {
            "id": "thai-orchid",
            "name": "Thai Orchid",
            "cuisine_type": "Thai",
            "rating": 4.5,
            "delivery_time": "30-45 min",
            "delivery_fee": 2.99,
            "image_url": "https://picsum.photos/seed/thai-orchid/400/300",
            "address": "222 Tenderloin Rd, San Francisco, CA 94102",
            "description": "Fragrant curries, pad thai, and soups that bring Bangkok to your door.",
        },
        {
            "id": "bella-italia",
            "name": "Bella Italia",
            "cuisine_type": "Italian",
            "rating": 4.6,
            "delivery_time": "25-40 min",
            "delivery_fee": 2.49,
            "image_url": "https://picsum.photos/seed/bella-italia/400/300",
            "address": "500 North Beach Rd, San Francisco, CA 94133",
            "description": "Classic Roman pasta, risotto, and tiramisu from a family recipe going back three generations.",
        },
    ]

    _menu: List[dict] = [
        # ------------------------------------------------------------------
        # Pizza Palace
        # ------------------------------------------------------------------
        {"id": "pp-001", "restaurant_id": "pizza-palace", "name": "Margherita Pizza", "description": "San Marzano tomatoes, fresh mozzarella, fragrant basil.", "price": 14.99, "category": "Mains", "image_url": "https://picsum.photos/seed/margherita/300/200"},
        {"id": "pp-002", "restaurant_id": "pizza-palace", "name": "Pepperoni Pizza", "description": "Loaded with premium pepperoni slices and melted mozzarella.", "price": 16.99, "category": "Mains", "image_url": "https://picsum.photos/seed/pepperoni/300/200"},
        {"id": "pp-003", "restaurant_id": "pizza-palace", "name": "BBQ Chicken Pizza", "description": "Smoky BBQ sauce, grilled chicken, red onion, cilantro.", "price": 17.99, "category": "Mains", "image_url": "https://picsum.photos/seed/bbqchicken/300/200"},
        {"id": "pp-004", "restaurant_id": "pizza-palace", "name": "Garlic Bread", "description": "House-baked focaccia with roasted garlic and herbs.", "price": 5.99, "category": "Appetizers", "image_url": "https://picsum.photos/seed/garlicbread/300/200"},
        {"id": "pp-005", "restaurant_id": "pizza-palace", "name": "Caesar Salad", "description": "Romaine, shaved Parmesan, croutons, classic Caesar dressing.", "price": 8.99, "category": "Appetizers", "image_url": "https://picsum.photos/seed/caesarsalad/300/200"},
        {"id": "pp-006", "restaurant_id": "pizza-palace", "name": "Tiramisu", "description": "Light espresso-soaked ladyfingers with mascarpone cream.", "price": 6.99, "category": "Desserts", "image_url": "https://picsum.photos/seed/tiramisu/300/200"},
        {"id": "pp-007", "restaurant_id": "pizza-palace", "name": "Soda", "description": "Coke, Diet Coke, Sprite, or Lemonade.", "price": 2.49, "category": "Drinks", "image_url": "https://picsum.photos/seed/soda/300/200"},

        # ------------------------------------------------------------------
        # Dragon Wok
        # ------------------------------------------------------------------
        {"id": "dw-001", "restaurant_id": "dragon-wok", "name": "Kung Pao Chicken", "description": "Wok-tossed chicken with peanuts, dried chillies, and scallions.", "price": 13.99, "category": "Mains", "image_url": "https://picsum.photos/seed/kungpao/300/200"},
        {"id": "dw-002", "restaurant_id": "dragon-wok", "name": "Beef Fried Rice", "description": "Fragrant jasmine rice, tender beef strips, egg, and vegetables.", "price": 12.99, "category": "Mains", "image_url": "https://picsum.photos/seed/friedrice/300/200"},
        {"id": "dw-003", "restaurant_id": "dragon-wok", "name": "Dim Sum Basket", "description": "Assorted steamed dumplings — pork, shrimp, and veggie.", "price": 9.99, "category": "Appetizers", "image_url": "https://picsum.photos/seed/dimsum/300/200"},
        {"id": "dw-004", "restaurant_id": "dragon-wok", "name": "Hot & Sour Soup", "description": "Traditional Sichuan broth with tofu, mushrooms, and bamboo shoots.", "price": 5.99, "category": "Appetizers", "image_url": "https://picsum.photos/seed/hotsoursoup/300/200"},
        {"id": "dw-005", "restaurant_id": "dragon-wok", "name": "Mapo Tofu", "description": "Silken tofu in a fiery bean paste sauce with ground pork.", "price": 11.99, "category": "Mains", "image_url": "https://picsum.photos/seed/mapotofu/300/200"},
        {"id": "dw-006", "restaurant_id": "dragon-wok", "name": "Mango Pudding", "description": "Creamy chilled mango pudding topped with evaporated milk.", "price": 4.99, "category": "Desserts", "image_url": "https://picsum.photos/seed/mangopudding/300/200"},
        {"id": "dw-007", "restaurant_id": "dragon-wok", "name": "Jasmine Tea", "description": "Pot of freshly brewed jasmine green tea.", "price": 2.99, "category": "Drinks", "image_url": "https://picsum.photos/seed/jasminetea/300/200"},

        # ------------------------------------------------------------------
        # Taco Fiesta
        # ------------------------------------------------------------------
        {"id": "tf-001", "restaurant_id": "taco-fiesta", "name": "Street Tacos (3)", "description": "Three corn tortilla tacos — your choice of carne asada, al pastor, or chicken.", "price": 10.99, "category": "Mains", "image_url": "https://picsum.photos/seed/streettacos/300/200"},
        {"id": "tf-002", "restaurant_id": "taco-fiesta", "name": "Burrito Bowl", "description": "Rice, beans, cheese, pico de gallo, guacamole, sour cream.", "price": 12.99, "category": "Mains", "image_url": "https://picsum.photos/seed/burritobowl/300/200"},
        {"id": "tf-003", "restaurant_id": "taco-fiesta", "name": "Chicken Quesadilla", "description": "Flour tortilla stuffed with grilled chicken and melted cheddar.", "price": 11.49, "category": "Mains", "image_url": "https://picsum.photos/seed/quesadilla/300/200"},
        {"id": "tf-004", "restaurant_id": "taco-fiesta", "name": "Chips & Guacamole", "description": "House-made tortilla chips with fresh chunky guacamole.", "price": 5.99, "category": "Appetizers", "image_url": "https://picsum.photos/seed/guacamole/300/200"},
        {"id": "tf-005", "restaurant_id": "taco-fiesta", "name": "Elote (Corn)", "description": "Grilled street corn with cotija, chili, lime, and crema.", "price": 4.99, "category": "Sides", "image_url": "https://picsum.photos/seed/elote/300/200"},
        {"id": "tf-006", "restaurant_id": "taco-fiesta", "name": "Churros", "description": "Crispy cinnamon sugar churros with chocolate dipping sauce.", "price": 5.49, "category": "Desserts", "image_url": "https://picsum.photos/seed/churros/300/200"},
        {"id": "tf-007", "restaurant_id": "taco-fiesta", "name": "Horchata", "description": "Chilled rice milk sweetened with cinnamon and vanilla.", "price": 3.49, "category": "Drinks", "image_url": "https://picsum.photos/seed/horchata/300/200"},

        # ------------------------------------------------------------------
        # Sakura Sushi
        # ------------------------------------------------------------------
        {"id": "ss-001", "restaurant_id": "sakura-sushi", "name": "Dragon Roll", "description": "Shrimp tempura inside, avocado on top, eel sauce drizzle.", "price": 15.99, "category": "Mains", "image_url": "https://picsum.photos/seed/dragonroll/300/200"},
        {"id": "ss-002", "restaurant_id": "sakura-sushi", "name": "Salmon Nigiri (2 pc)", "description": "Hand-pressed sushi rice topped with premium Atlantic salmon.", "price": 7.99, "category": "Mains", "image_url": "https://picsum.photos/seed/salmonnigiri/300/200"},
        {"id": "ss-003", "restaurant_id": "sakura-sushi", "name": "Spicy Tuna Roll", "description": "Tuna, sriracha aioli, cucumber, sesame seeds.", "price": 13.99, "category": "Mains", "image_url": "https://picsum.photos/seed/spicytuna/300/200"},
        {"id": "ss-004", "restaurant_id": "sakura-sushi", "name": "Edamame", "description": "Steamed salted edamame pods.", "price": 4.99, "category": "Appetizers", "image_url": "https://picsum.photos/seed/edamame/300/200"},
        {"id": "ss-005", "restaurant_id": "sakura-sushi", "name": "Miso Soup", "description": "Classic dashi broth with tofu, wakame, and scallion.", "price": 3.99, "category": "Appetizers", "image_url": "https://picsum.photos/seed/misosoup/300/200"},
        {"id": "ss-006", "restaurant_id": "sakura-sushi", "name": "Mochi Ice Cream", "description": "Three-piece assorted mochi: strawberry, green tea, mango.", "price": 6.99, "category": "Desserts", "image_url": "https://picsum.photos/seed/mochi/300/200"},
        {"id": "ss-007", "restaurant_id": "sakura-sushi", "name": "Green Tea", "description": "Hot or iced traditional Japanese matcha green tea.", "price": 2.99, "category": "Drinks", "image_url": "https://picsum.photos/seed/greentea/300/200"},

        # ------------------------------------------------------------------
        # Taj Mahal Kitchen
        # ------------------------------------------------------------------
        {"id": "tm-001", "restaurant_id": "taj-mahal-kitchen", "name": "Butter Chicken", "description": "Tender chicken in a velvety tomato-butter-cream sauce.", "price": 14.99, "category": "Mains", "image_url": "https://picsum.photos/seed/butterchicken/300/200"},
        {"id": "tm-002", "restaurant_id": "taj-mahal-kitchen", "name": "Lamb Biryani", "description": "Slow-cooked basmati rice with spiced braised lamb and saffron.", "price": 16.99, "category": "Mains", "image_url": "https://picsum.photos/seed/biryani/300/200"},
        {"id": "tm-003", "restaurant_id": "taj-mahal-kitchen", "name": "Palak Paneer", "description": "Fresh spinach purée with house-made paneer cheese.", "price": 13.49, "category": "Mains", "image_url": "https://picsum.photos/seed/palakpaneer/300/200"},
        {"id": "tm-004", "restaurant_id": "taj-mahal-kitchen", "name": "Samosa (2 pc)", "description": "Crispy pastry filled with spiced potato and peas.", "price": 5.99, "category": "Appetizers", "image_url": "https://picsum.photos/seed/samosa/300/200"},
        {"id": "tm-005", "restaurant_id": "taj-mahal-kitchen", "name": "Garlic Naan", "description": "Tandoor-baked flatbread brushed with garlic butter.", "price": 3.99, "category": "Sides", "image_url": "https://picsum.photos/seed/naan/300/200"},
        {"id": "tm-006", "restaurant_id": "taj-mahal-kitchen", "name": "Gulab Jamun", "description": "Milk-solid dumplings soaked in rose-flavored sugar syrup.", "price": 5.49, "category": "Desserts", "image_url": "https://picsum.photos/seed/gulabjamun/300/200"},
        {"id": "tm-007", "restaurant_id": "taj-mahal-kitchen", "name": "Mango Lassi", "description": "Cool blended yogurt drink with Alphonso mango pulp.", "price": 3.99, "category": "Drinks", "image_url": "https://picsum.photos/seed/mangolassi/300/200"},

        # ------------------------------------------------------------------
        # Burger Barn
        # ------------------------------------------------------------------
        {"id": "bb-001", "restaurant_id": "burger-barn", "name": "Classic Smash Burger", "description": "Double smashed patties, American cheese, pickles, special sauce.", "price": 12.99, "category": "Mains", "image_url": "https://picsum.photos/seed/smashburger/300/200"},
        {"id": "bb-002", "restaurant_id": "burger-barn", "name": "Bacon BBQ Burger", "description": "Beef patty, crispy bacon, cheddar, onion rings, BBQ sauce.", "price": 14.49, "category": "Mains", "image_url": "https://picsum.photos/seed/bbqburger/300/200"},
        {"id": "bb-003", "restaurant_id": "burger-barn", "name": "Veggie Burger", "description": "Black bean patty with avocado, lettuce, tomato, jalapeño mayo.", "price": 12.49, "category": "Mains", "image_url": "https://picsum.photos/seed/veggieburger/300/200"},
        {"id": "bb-004", "restaurant_id": "burger-barn", "name": "Onion Rings", "description": "Beer-battered jumbo onion rings with ranch dipping sauce.", "price": 5.99, "category": "Sides", "image_url": "https://picsum.photos/seed/onionrings/300/200"},
        {"id": "bb-005", "restaurant_id": "burger-barn", "name": "Crispy Fries", "description": "Golden shoestring fries seasoned with sea salt.", "price": 3.99, "category": "Sides", "image_url": "https://picsum.photos/seed/crispyfries/300/200"},
        {"id": "bb-006", "restaurant_id": "burger-barn", "name": "Chocolate Milkshake", "description": "Thick hand-spun shake with premium chocolate ice cream.", "price": 6.49, "category": "Drinks", "image_url": "https://picsum.photos/seed/chocolateshake/300/200"},
        {"id": "bb-007", "restaurant_id": "burger-barn", "name": "Apple Pie Slice", "description": "Warm homestyle apple pie with a scoop of vanilla ice cream.", "price": 5.49, "category": "Desserts", "image_url": "https://picsum.photos/seed/applepie/300/200"},

        # ------------------------------------------------------------------
        # Thai Orchid
        # ------------------------------------------------------------------
        {"id": "to-001", "restaurant_id": "thai-orchid", "name": "Pad Thai", "description": "Rice noodles, egg, tofu or shrimp, bean sprouts, peanuts, lime.", "price": 13.99, "category": "Mains", "image_url": "https://picsum.photos/seed/padthai/300/200"},
        {"id": "to-002", "restaurant_id": "thai-orchid", "name": "Green Curry", "description": "Coconut milk green curry with your choice of protein and Thai basil.", "price": 14.49, "category": "Mains", "image_url": "https://picsum.photos/seed/greencurry/300/200"},
        {"id": "to-003", "restaurant_id": "thai-orchid", "name": "Tom Yum Soup", "description": "Spicy-sour lemongrass broth with shrimp, mushrooms, and galangal.", "price": 8.99, "category": "Appetizers", "image_url": "https://picsum.photos/seed/tomyum/300/200"},
        {"id": "to-004", "restaurant_id": "thai-orchid", "name": "Spring Rolls (4 pc)", "description": "Crispy vegetable spring rolls served with sweet chilli sauce.", "price": 6.99, "category": "Appetizers", "image_url": "https://picsum.photos/seed/springrolls/300/200"},
        {"id": "to-005", "restaurant_id": "thai-orchid", "name": "Massaman Curry", "description": "Rich slow-cooked curry with potato, peanuts, and coconut milk.", "price": 14.99, "category": "Mains", "image_url": "https://picsum.photos/seed/massamancurry/300/200"},
        {"id": "to-006", "restaurant_id": "thai-orchid", "name": "Mango Sticky Rice", "description": "Sweet glutinous rice with fresh mango and coconut cream.", "price": 6.99, "category": "Desserts", "image_url": "https://picsum.photos/seed/mangostickyrice/300/200"},
        {"id": "to-007", "restaurant_id": "thai-orchid", "name": "Thai Iced Tea", "description": "Sweetened strong tea with condensed milk over ice.", "price": 3.99, "category": "Drinks", "image_url": "https://picsum.photos/seed/thaiicedtea/300/200"},

        # ------------------------------------------------------------------
        # Bella Italia
        # ------------------------------------------------------------------
        {"id": "bi-001", "restaurant_id": "bella-italia", "name": "Spaghetti Carbonara", "description": "Al dente spaghetti, guanciale, egg yolk, Pecorino Romano, black pepper.", "price": 15.99, "category": "Mains", "image_url": "https://picsum.photos/seed/carbonara/300/200"},
        {"id": "bi-002", "restaurant_id": "bella-italia", "name": "Penne all'Arrabbiata", "description": "Penne with a fiery tomato-garlic-chilli sauce.", "price": 13.49, "category": "Mains", "image_url": "https://picsum.photos/seed/arrabbiata/300/200"},
        {"id": "bi-003", "restaurant_id": "bella-italia", "name": "Osso Buco", "description": "Braised veal shank with gremolata and saffron risotto.", "price": 22.99, "category": "Mains", "image_url": "https://picsum.photos/seed/ossobuco/300/200"},
        {"id": "bi-004", "restaurant_id": "bella-italia", "name": "Bruschetta al Pomodoro", "description": "Grilled sourdough topped with fresh tomato, basil, and olive oil.", "price": 6.99, "category": "Appetizers", "image_url": "https://picsum.photos/seed/bruschetta/300/200"},
        {"id": "bi-005", "restaurant_id": "bella-italia", "name": "Arancini (3 pc)", "description": "Crispy risotto balls stuffed with mozzarella and marinara.", "price": 8.99, "category": "Appetizers", "image_url": "https://picsum.photos/seed/arancini/300/200"},
        {"id": "bi-006", "restaurant_id": "bella-italia", "name": "Tiramisu", "description": "Classic Italian dessert with espresso-soaked ladyfingers and mascarpone.", "price": 7.49, "category": "Desserts", "image_url": "https://picsum.photos/seed/bellaitaliarooms/300/200"},
        {"id": "bi-007", "restaurant_id": "bella-italia", "name": "San Pellegrino", "description": "Sparkling or still mineral water, 500 ml.", "price": 2.99, "category": "Drinks", "image_url": "https://picsum.photos/seed/sanpellegrino/300/200"},
    ]

    for r in _restaurants:
        restaurants_db[r["id"]] = r

    for item in _menu:
        menu_items_db[item["id"]] = item


# Run seed on import so every router has data the moment it imports models.
seed_data()
