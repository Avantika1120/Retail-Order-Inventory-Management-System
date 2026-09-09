"""Seed a small retail dataset for local demos.

Run after PostgreSQL and MongoDB are available:
    cd backend
    PYTHONPATH=. python seed_demo.py
"""

from decimal import Decimal

from sqlalchemy import select

from app.db.mongo import mongo_db
from app.db.postgres import Base, SessionLocal, engine
from app.models.models import Customer, Inventory, Order, OrderItem, Product


PRODUCTS = [
    ("ELEC-001", "Noise-Cancelling Headphones", "Electronics", Decimal("149.99"), 24),
    ("HOME-002", "Smart LED Desk Lamp", "Home", Decimal("39.99"), 8),
    ("FIT-003", "Insulated Water Bottle", "Fitness", Decimal("27.50"), 42),
]

CUSTOMERS = [
    ("Maya Thompson", "maya@example.com"),
    ("Daniel Kim", "daniel@example.com"),
]

REVIEWS = [
    {"sku": "ELEC-001", "customer_id": 1, "rating": 5, "title": "Great for travel", "body": "Noise cancellation is excellent and the battery lasts through long flights."},
    {"sku": "ELEC-001", "customer_id": 2, "rating": 4, "title": "Strong sound, tight fit", "body": "Sound quality is clear, but the headband feels tight after a few hours."},
    {"sku": "HOME-002", "customer_id": 1, "rating": 4, "title": "Useful desk light", "body": "Brightness controls are convenient and setup was simple."},
]


def main() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        for sku, name, category, price, stock in PRODUCTS:
            product = db.scalar(select(Product).where(Product.sku == sku))
            if not product:
                product = Product(sku=sku, name=name, category=category, price=price)
                product.inventory = Inventory(quantity_on_hand=stock, reorder_level=10)
                db.add(product)

        for name, email in CUSTOMERS:
            if not db.scalar(select(Customer).where(Customer.email == email)):
                db.add(Customer(name=name, email=email))

        db.commit()

        first_customer = db.scalar(select(Customer).order_by(Customer.id))
        first_product = db.scalar(select(Product).where(Product.sku == "FIT-003"))
        existing_order = db.scalar(select(Order).limit(1))
        if first_customer and first_product and not existing_order:
            order = Order(customer_id=first_customer.id, status="completed", total_amount=first_product.price * 2)
            order.items.append(OrderItem(product_id=first_product.id, quantity=2, unit_price=first_product.price, line_total=first_product.price * 2))
            first_product.inventory.quantity_on_hand -= 2
            db.add(order)
            db.commit()

        products_by_sku = {p.sku: p.id for p in db.scalars(select(Product))}

    for review in REVIEWS:
        product_id = products_by_sku[review["sku"]]
        if not mongo_db.reviews.find_one({"product_id": product_id, "title": review["title"]}):
            mongo_db.reviews.insert_one({
                "product_id": product_id,
                "customer_id": review["customer_id"],
                "rating": review["rating"],
                "title": review["title"],
                "body": review["body"],
            })

    print("Demo data seeded successfully.")


if __name__ == "__main__":
    main()
