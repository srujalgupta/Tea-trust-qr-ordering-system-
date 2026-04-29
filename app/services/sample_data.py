from decimal import Decimal

from app.extensions import db
from app.models import CafeTable, Category, MenuItem
from .auth_service import ensure_admin_user


CATEGORIES = [
    ("Tea With Milk", 1),
    ("Tea Without Milk", 2),
    ("Iced Tea", 3),
    ("Quick Bites", 4),
    ("Kathiyawadi Bites", 5),
    ("Open Toast", 6),
    ("Brown Bread Sandwich", 7),
    ("Burger", 8),
    ("Zero Oil Fries", 9),
    ("Hot Coffee & Milk", 10),
    ("Cold & Iced Coffee", 11),
    ("Mocktails", 12),
    ("Classical Shakes", 13),
    ("Signature Shakes", 14),
    ("Maggi Noodles", 15),
    ("Add On", 16),
]


MENU_ITEMS = [
    ("Tea With Milk", "Masala Tea (Half)", 25, "tea, half"),
    ("Tea With Milk", "Masala Tea (Full)", 40, "tea, full"),
    ("Tea With Milk", "Ginger Tea (Half)", 25, "tea, half"),
    ("Tea With Milk", "Ginger Tea (Full)", 40, "tea, full"),
    ("Tea With Milk", "Ginger Elaichi Tea (Half)", 25, "tea, half"),
    ("Tea With Milk", "Ginger Elaichi Tea (Full)", 40, "tea, full"),
    ("Tea With Milk", "Ginger Pudina Tea (Half)", 25, "tea, half"),
    ("Tea With Milk", "Ginger Pudina Tea (Full)", 40, "tea, full"),
    ("Tea With Milk", "Ginger Lemongrass Tea (Half)", 25, "tea, half"),
    ("Tea With Milk", "Ginger Lemongrass Tea (Full)", 40, "tea, full"),
    ("Tea With Milk", "Pudina Tea (Half)", 25, "tea, half"),
    ("Tea With Milk", "Pudina Tea (Full)", 40, "tea, full"),
    ("Tea With Milk", "Tulasi Tea (Half)", 25, "tea, half"),
    ("Tea With Milk", "Tulasi Tea (Full)", 40, "tea, full"),
    ("Tea With Milk", "Ginger Tulasi Tea (Half)", 25, "tea, half"),
    ("Tea With Milk", "Ginger Tulasi Tea (Full)", 40, "tea, full"),
    ("Tea With Milk", "Cinnamon Tea (Half)", 25, "tea, half"),
    ("Tea With Milk", "Cinnamon Tea (Full)", 40, "tea, full"),
    ("Tea With Milk", "Elaichi Tea (Half)", 25, "tea, half"),
    ("Tea With Milk", "Elaichi Tea (Full)", 40, "tea, full"),
    ("Tea With Milk", "Kesar Elaichy Tea (Half)", 30, "tea, half"),
    ("Tea With Milk", "Kesar Elaichy Tea (Full)", 45, "tea, full"),
    ("Tea Without Milk", "Black Lemon Tea", 25, "tea"),
    ("Tea Without Milk", "Black Lemon Ginger Tea", 30, "tea"),
    ("Tea Without Milk", "Darjeeling Lemon Tea", 30, "tea"),
    ("Tea Without Milk", "Darjeeling Lemon Ginger Tea", 35, "tea"),
    ("Tea Without Milk", "Green Lemon Tea", 35, "tea"),
    ("Tea Without Milk", "Organic Tulsi Tea", 35, "tea"),
    ("Tea Without Milk", "Green Lemon Ginger Tea", 40, "tea"),
    ("Iced Tea", "Green Ice Tea", 60, "iced tea"),
    ("Iced Tea", "Fresh Lime Water", 60, "lime"),
    ("Iced Tea", "Peach Ice Tea", 70, "iced tea"),
    ("Iced Tea", "Lemon Ice Tea", 70, "iced tea"),
    ("Iced Tea", "Muskmelon Ice Tea", 75, "iced tea"),
    ("Iced Tea", "Mixed Berries Ice Tea", 75, "iced tea"),
    ("Quick Bites", "Bread Butter Toast", 25, "toast"),
    ("Quick Bites", "Maska Bun", 25, "bun"),
    ("Quick Bites", "Maska Bun Jam", 30, "bun"),
    ("Quick Bites", "Hot Wheat Khari", 30, "khari"),
    ("Quick Bites", "Bread Butter", 35, "bread"),
    ("Quick Bites", "Bread Butter Jam", 40, "bread"),
    ("Kathiyawadi Bites", "Methi Masala Khakhra (2 Pcs)", 29, "khakhra"),
    ("Kathiyawadi Bites", "Bhakhri (1 Pcs)", 29, "bhakhri"),
    ("Kathiyawadi Bites", "Methi Masala Bhakhri (1 Pcs)", 39, "bhakhri"),
    ("Kathiyawadi Bites", "Thepla (2 Pcs)", 49, "thepla"),
    ("Open Toast", "Chilly Cheese Toast", 60, "toast, spicy"),
    ("Open Toast", "Chilly Cheese Garlic Toast", 70, "toast, spicy"),
    ("Open Toast", "Veg. Supreme Toast", 70, "toast"),
    ("Open Toast", "Corn Cheese Toast", 70, "toast"),
    ("Open Toast", "Garlic Bread", 99, "garlic bread"),
    ("Brown Bread Sandwich", "Italian Sandwich (Grilled)", 70, "sandwich, grilled"),
    ("Brown Bread Sandwich", "Coleslow Sandwich (Grilled)", 70, "sandwich, grilled"),
    ("Brown Bread Sandwich", "Coleslow Sandwich (Plain)", 60, "sandwich, plain"),
    ("Brown Bread Sandwich", "Veg. Sandwich (Grilled)", 75, "sandwich, grilled"),
    ("Brown Bread Sandwich", "Veg. Sandwich (Plain)", 60, "sandwich, plain"),
    ("Brown Bread Sandwich", "Veg. Cheese Sandwich (Grilled)", 85, "sandwich, grilled"),
    ("Brown Bread Sandwich", "Veg. Cheese Sandwich (Plain)", 70, "sandwich, plain"),
    ("Brown Bread Sandwich", "Cheese Corn Sandwich (Grilled)", 90, "sandwich, grilled"),
    ("Brown Bread Sandwich", "Cheese Chutney Sandwich (Grilled)", 90, "sandwich, grilled"),
    ("Brown Bread Sandwich", "Cheese Chutney Sandwich (Plain)", 70, "sandwich, plain"),
    ("Brown Bread Sandwich", "Chocolate Sandwich (Grilled)", 90, "sandwich, grilled"),
    ("Brown Bread Sandwich", "Club Sandwich (Grilled)", 110, "sandwich, grilled"),
    ("Brown Bread Sandwich", "Peri Peri Paneer Sandwich (Grilled)", 110, "sandwich, grilled, spicy"),
    ("Brown Bread Sandwich", "Tandoori Paneer Sandwich (Grilled)", 110, "sandwich, grilled"),
    ("Brown Bread Sandwich", "Maxican Sandwich (Grilled)", 149, "sandwich, grilled"),
    ("Brown Bread Sandwich", "Heritage Sandwich (Grilled)", 149, "sandwich, grilled, spicy"),
    ("Burger", "Veg Classic Burger", 59, "burger"),
    ("Burger", "Veg Cheese Classic Burger", 79, "burger"),
    ("Burger", "Peri Peri Burger", 99, "burger, spicy"),
    ("Burger", "Melting Cheese Burger", 99, "burger"),
    ("Burger", "Paneer Tandoori Burger", 99, "burger"),
    ("Zero Oil Fries", "French Fries (With Oil)", 95, "fries"),
    ("Zero Oil Fries", "French Fries (Zero Oil)", 105, "fries, zero oil"),
    ("Zero Oil Fries", "Masala French Fries (With Oil)", 95, "fries, spicy"),
    ("Zero Oil Fries", "Masala French Fries (Zero Oil)", 105, "fries, spicy, zero oil"),
    ("Zero Oil Fries", "Potato Wedges (With Oil)", 95, "fries"),
    ("Zero Oil Fries", "Potato Wedges (Zero Oil)", 105, "fries, zero oil"),
    ("Zero Oil Fries", "Popcorn Fries (With Oil)", 95, "fries"),
    ("Zero Oil Fries", "Popcorn Fries (Zero Oil)", 105, "fries, zero oil"),
    ("Zero Oil Fries", "Chilly Garlic Potato Balls (With Oil)", 95, "fries, spicy"),
    ("Zero Oil Fries", "Chilly Garlic Potato Balls (Zero Oil)", 105, "fries, spicy, zero oil"),
    ("Zero Oil Fries", "Smiles (With Oil)", 95, "fries"),
    ("Zero Oil Fries", "Smiles (Zero Oil)", 105, "fries, zero oil"),
    ("Zero Oil Fries", "V Crispers (With Oil)", 95, "fries"),
    ("Zero Oil Fries", "V Crispers (Zero Oil)", 105, "fries, zero oil"),
    ("Zero Oil Fries", "Veggie Nuggets (With Oil)", 95, "fries"),
    ("Zero Oil Fries", "Veggie Nuggets (Zero Oil)", 105, "fries, zero oil"),
    ("Zero Oil Fries", "Veggie Fingers (With Oil)", 95, "fries"),
    ("Zero Oil Fries", "Veggie Fingers (Zero Oil)", 105, "fries, zero oil"),
    ("Zero Oil Fries", "Crispons (With Oil)", 95, "fries"),
    ("Zero Oil Fries", "Crispons (Zero Oil)", 105, "fries, zero oil"),
    ("Zero Oil Fries", "Potato Cheese Shotz (With Oil)", 95, "fries"),
    ("Zero Oil Fries", "Potato Cheese Shotz (Zero Oil)", 105, "fries, zero oil"),
    ("Zero Oil Fries", "Cheese Pizza Triangle (With Oil)", 95, "fries"),
    ("Zero Oil Fries", "Cheese Pizza Triangle (Zero Oil)", 105, "fries, zero oil"),
    ("Zero Oil Fries", "Cheese Jalapeno Triangle (With Oil)", 95, "fries"),
    ("Zero Oil Fries", "Cheese Jalapeno Triangle (Zero Oil)", 105, "fries, zero oil"),
    ("Zero Oil Fries", "Cheese Corn Triangle (With Oil)", 95, "fries"),
    ("Zero Oil Fries", "Cheese Corn Triangle (Zero Oil)", 105, "fries, zero oil"),
    ("Hot Coffee & Milk", "Black Coffee", 40, "coffee"),
    ("Hot Coffee & Milk", "Hot Bournvita", 40, "milk"),
    ("Hot Coffee & Milk", "Hot Coffee", 45, "coffee"),
    ("Hot Coffee & Milk", "Hot Chocolate", 50, "milk"),
    ("Hot Coffee & Milk", "Hot Kesar Masala Milk", 50, "milk"),
    ("Cold & Iced Coffee", "Cold Kesar Masala Milk", 50, "milk"),
    ("Cold & Iced Coffee", "Choco Fiesta", 60, "coffee"),
    ("Cold & Iced Coffee", "Black Iced Coffee", 60, "coffee"),
    ("Cold & Iced Coffee", "Cold Bournvita", 70, "milk"),
    ("Cold & Iced Coffee", "Cold Coffee", 75, "coffee"),
    ("Cold & Iced Coffee", "Caramel Cold Coffee", 95, "coffee"),
    ("Cold & Iced Coffee", "Cold Coffee Ice-Cream Blended", 95, "coffee"),
    ("Mocktails", "Mojito Mint", 80, "mocktail"),
    ("Mocktails", "Green Apple Mocktail", 80, "mocktail"),
    ("Mocktails", "Blue Curacao", 80, "mocktail"),
    ("Mocktails", "Black Current Mocktail", 80, "mocktail"),
    ("Mocktails", "Pomegranate Mocktail", 80, "mocktail"),
    ("Classical Shakes", "Classical Vanilla", 90, "shake"),
    ("Classical Shakes", "Strawberry Shake", 99, "shake"),
    ("Classical Shakes", "Black Current Shake", 99, "shake"),
    ("Classical Shakes", "Blue Berry Shake", 99, "shake"),
    ("Classical Shakes", "Classical Caramel", 99, "shake"),
    ("Classical Shakes", "Caramel Banana", 99, "shake"),
    ("Classical Shakes", "Guava Shake", 99, "shake"),
    ("Classical Shakes", "Pineapple Shake", 99, "shake"),
    ("Classical Shakes", "Lychee Shake", 99, "shake"),
    ("Classical Shakes", "Kiwi Shake", 99, "shake"),
    ("Classical Shakes", "Banana Shake", 99, "shake"),
    ("Classical Shakes", "Green Apple Shake", 99, "shake"),
    ("Signature Shakes", "Oreo Chocolate", 99, "shake"),
    ("Signature Shakes", "Caramel Oreo", 99, "shake"),
    ("Signature Shakes", "Kit Kat Shake", 99, "shake"),
    ("Signature Shakes", "Five Star Shake", 99, "shake"),
    ("Signature Shakes", "Snickers Shake", 99, "shake"),
    ("Signature Shakes", "Caramel Chocolate", 99, "shake"),
    ("Maggi Noodles", "Veg. Maggi Noodles", 60, "maggi"),
    ("Maggi Noodles", "Cheese Veg. Maggi Noodles", 80, "maggi"),
    ("Add On", "Cheese / Paneer Add On", 25, "add on"),
    ("Add On", "Honey Add On", 10, "add on"),
    ("Add On", "Chocolate Sauce Add On", 10, "add on"),
]


def _price(value):
    return Decimal(str(value)).quantize(Decimal("0.01"))


def _upsert_category(name, display_order):
    category = Category.query.filter_by(name=name).first()
    if not category:
        category = Category(name=name)
        db.session.add(category)
    category.display_order = display_order
    category.description = None
    category.is_active = True
    return category


def _upsert_menu_item(category, name, price, tags):
    item = MenuItem.query.filter_by(category_id=category.id, name=name).first()
    if not item:
        item = MenuItem(category=category, name=name)
        db.session.add(item)
    item.description = ""
    item.price = _price(price)
    item.tags = tags
    item.is_veg = True
    item.is_bestseller = False
    item.is_available = True
    return item


def seed_sample_data(config):
    admin, _ = ensure_admin_user(
        config["ADMIN_USERNAME"],
        config["ADMIN_PASSWORD"],
        config["ADMIN_EMAIL"],
    )

    active_category_names = {name for name, _ in CATEGORIES}
    active_item_keys = {(category_name, name) for category_name, name, _, _ in MENU_ITEMS}

    for category in Category.query.all():
        if category.name not in active_category_names:
            category.is_active = False

    categories = {}
    for name, display_order in CATEGORIES:
        categories[name] = _upsert_category(name, display_order)

    db.session.flush()

    for item in MenuItem.query.all():
        category_name = item.category.name if item.category else None
        if (category_name, item.name) not in active_item_keys:
            item.is_available = False

    for category_name, name, price, tags in MENU_ITEMS:
        _upsert_menu_item(categories[category_name], name, price, tags)

    table_count = int(config.get("CAFE_TABLE_COUNT", 6))
    for table_number in range(1, table_count + 1):
        table = CafeTable.query.filter_by(table_number=table_number).first()
        if not table:
            table = CafeTable(table_number=table_number)
            db.session.add(table)
        table.label = table.label or f"Table {table_number}"
        table.qr_slug = table.qr_slug or f"table-{table_number}"
        table.is_active = True

    for table in CafeTable.query.filter(CafeTable.table_number > table_count).all():
        table.is_active = False

    db.session.commit()
    return admin
