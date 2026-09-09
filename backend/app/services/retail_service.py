from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.mongo import mongo_db
from app.models.models import Customer, Inventory, Order, OrderItem, Product
from app.schemas.schemas import (
    CustomerCreate,
    CustomerUpdate,
    OrderCreate,
    ProductCreate,
    ProductUpdate,
)


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

    def update_product(self, product_id: int, payload: ProductUpdate) -> Product:
        product = self.db.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        for field, value in payload.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(product, field, value)
        self.db.commit()
        self.db.refresh(product)
        self._audit("product.updated", {"product_id": product_id})
        return product

    def delete_product(self, product_id: int) -> None:
        product = self.db.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        ordered = self.db.scalar(select(OrderItem.id).where(OrderItem.product_id == product_id).limit(1))
        if ordered:
            raise HTTPException(status_code=409, detail="Cannot delete a product referenced by an order")
        self.db.delete(product)
        self.db.commit()
        self._audit("product.deleted", {"product_id": product_id})

    def list_customers(self) -> list[Customer]:
        return list(self.db.scalars(select(Customer).order_by(Customer.id)))

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

    def update_customer(self, customer_id: int, payload: CustomerUpdate) -> Customer:
        customer = self.db.get(Customer, customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        values = payload.model_dump(exclude_unset=True)
        if values.get("email"):
            duplicate = self.db.scalar(
                select(Customer).where(Customer.email == str(values["email"]), Customer.id != customer_id)
            )
            if duplicate:
                raise HTTPException(status_code=409, detail="Customer email already exists")
            values["email"] = str(values["email"])
        for field, value in values.items():
            if value is not None:
                setattr(customer, field, value)
        self.db.commit()
        self.db.refresh(customer)
        self._audit("customer.updated", {"customer_id": customer_id})
        return customer

    def delete_customer(self, customer_id: int) -> None:
        customer = self.db.get(Customer, customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        ordered = self.db.scalar(select(Order.id).where(Order.customer_id == customer_id).limit(1))
        if ordered:
            raise HTTPException(status_code=409, detail="Cannot delete a customer with order history")
        self.db.delete(customer)
        self.db.commit()
        self._audit("customer.deleted", {"customer_id": customer_id})

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

    def update_order_status(self, order_id: int, status: str) -> Order:
        order = self.db.get(Order, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        allowed = {
            "created": {"processing", "cancelled"},
            "processing": {"shipped", "cancelled"},
            "shipped": {"completed"},
            "completed": set(),
            "cancelled": set(),
        }
        if status != order.status and status not in allowed.get(order.status, set()):
            raise HTTPException(status_code=409, detail=f"Invalid status transition: {order.status} -> {status}")
        order.status = status
        self.db.commit()
        self.db.refresh(order)
        self._audit("order.status_updated", {"order_id": order_id, "status": status})
        return order

    @staticmethod
    def _audit(event_type: str, payload: dict) -> None:
        mongo_db.audit_events.insert_one({"event_type": event_type, "payload": payload})
