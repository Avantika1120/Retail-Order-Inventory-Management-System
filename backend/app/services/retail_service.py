from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.mongo import mongo_db
from app.models.models import Customer, Inventory, Order, OrderItem, Product
from app.schemas.schemas import CustomerCreate, OrderCreate, ProductCreate


class RetailService:
    def __init__(self, db: Session):
        self.db = db

    def list_products(self) -> list[Product]:
        return list(self.db.scalars(select(Product).order_by(Product.id)))

    def create_product(self, payload: ProductCreate) -> Product:
        existing = self.db.scalar(select(Product).where(Product.sku == payload.sku))
        if existing:
            raise HTTPException(status_code=409, detail="SKU already exists")

        product = Product(
            sku=payload.sku,
            name=payload.name,
            category=payload.category,
            price=payload.price,
        )
        product.inventory = Inventory(
            quantity_on_hand=payload.opening_stock,
            reorder_level=payload.reorder_level,
        )
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        self._audit("product.created", {"product_id": product.id, "sku": product.sku})
        return product

    def create_customer(self, payload: CustomerCreate) -> Customer:
        existing = self.db.scalar(select(Customer).where(Customer.email == payload.email))
        if existing:
            raise HTTPException(status_code=409, detail="Customer email already exists")
        customer = Customer(name=payload.name, email=str(payload.email))
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        self._audit("customer.created", {"customer_id": customer.id})
        return customer

    def list_inventory(self) -> list[Inventory]:
        return list(self.db.scalars(select(Inventory).order_by(Inventory.product_id)))

    def restock(self, product_id: int, quantity: int) -> Inventory:
        inventory = self.db.get(Inventory, product_id)
        if not inventory:
            raise HTTPException(status_code=404, detail="Inventory record not found")
        inventory.quantity_on_hand += quantity
        self.db.commit()
        self.db.refresh(inventory)
        self._audit("inventory.restocked", {"product_id": product_id, "quantity": quantity})
        return inventory

    def create_order(self, payload: OrderCreate) -> Order:
        if not payload.items:
            raise HTTPException(status_code=400, detail="Order must contain at least one item")
        if not self.db.get(Customer, payload.customer_id):
            raise HTTPException(status_code=404, detail="Customer not found")

        order = Order(customer_id=payload.customer_id, status="created", total_amount=Decimal("0"))
        total = Decimal("0")
        self.db.add(order)
        self.db.flush()

        try:
            for requested in payload.items:
                product = self.db.get(Product, requested.product_id)
                if not product:
                    raise HTTPException(status_code=404, detail=f"Product {requested.product_id} not found")

                inventory = self.db.execute(
                    select(Inventory).where(Inventory.product_id == requested.product_id).with_for_update()
                ).scalar_one_or_none()
                if not inventory or inventory.quantity_on_hand < requested.quantity:
                    available = inventory.quantity_on_hand if inventory else 0
                    raise HTTPException(
                        status_code=409,
                        detail=f"Insufficient stock for product {requested.product_id}; available={available}",
                    )

                line_total = product.price * requested.quantity
                total += line_total
                inventory.quantity_on_hand -= requested.quantity
                order.items.append(
                    OrderItem(
                        product_id=product.id,
                        quantity=requested.quantity,
                        unit_price=product.price,
                        line_total=line_total,
                    )
                )

            order.total_amount = total
            self.db.commit()
            self.db.refresh(order)
        except Exception:
            self.db.rollback()
            raise

        self._audit("order.created", {"order_id": order.id, "customer_id": order.customer_id, "total": str(total)})
        return order

    def list_orders(self) -> list[Order]:
        return list(self.db.scalars(select(Order).order_by(Order.created_at.desc())))

    @staticmethod
    def _audit(event_type: str, payload: dict) -> None:
        mongo_db.audit_events.insert_one({"event_type": event_type, "payload": payload})
