from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.db.postgres import get_db
from app.schemas.schemas import (
    CustomerCreate,
    CustomerRead,
    CustomerUpdate,
    InventoryRead,
    OrderCreate,
    OrderRead,
    OrderStatusUpdate,
    ProductCreate,
    ProductRead,
    ProductUpdate,
    RestockRequest,
    ReviewCreate,
    ReviewRead,
    ReviewSummary,
)
from app.services.retail_service import RetailService
from app.services.review_service import ReviewService

router = APIRouter(prefix="/api")


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/products", response_model=list[ProductRead])
def list_products(db: Session = Depends(get_db)):
    return RetailService(db).list_products()


@router.post("/products", response_model=ProductRead, status_code=201)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    return RetailService(db).create_product(payload)


@router.patch("/products/{product_id}", response_model=ProductRead)
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)):
    return RetailService(db).update_product(product_id, payload)


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    RetailService(db).delete_product(product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/customers", response_model=list[CustomerRead])
def list_customers(db: Session = Depends(get_db)):
    return RetailService(db).list_customers()


@router.post("/customers", response_model=CustomerRead, status_code=201)
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db)):
    return RetailService(db).create_customer(payload)


@router.patch("/customers/{customer_id}", response_model=CustomerRead)
def update_customer(customer_id: int, payload: CustomerUpdate, db: Session = Depends(get_db)):
    return RetailService(db).update_customer(customer_id, payload)


@router.delete("/customers/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    RetailService(db).delete_customer(customer_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/inventory", response_model=list[InventoryRead])
def list_inventory(db: Session = Depends(get_db)):
    return RetailService(db).list_inventory()


@router.post("/inventory/{product_id}/restock", response_model=InventoryRead)
def restock(product_id: int, payload: RestockRequest, db: Session = Depends(get_db)):
    return RetailService(db).restock(product_id, payload.quantity)


@router.get("/orders", response_model=list[OrderRead])
def list_orders(db: Session = Depends(get_db)):
    return RetailService(db).list_orders()


@router.post("/orders", response_model=OrderRead, status_code=201)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    return RetailService(db).create_order(payload)


@router.patch("/orders/{order_id}/status", response_model=OrderRead)
def update_order_status(order_id: int, payload: OrderStatusUpdate, db: Session = Depends(get_db)):
    return RetailService(db).update_order_status(order_id, payload.status)


@router.get("/products/{product_id}/reviews", response_model=list[ReviewRead])
def list_reviews(product_id: int):
    return ReviewService().list_reviews(product_id)


@router.post("/reviews", response_model=ReviewRead, status_code=201)
def create_review(payload: ReviewCreate):
    return ReviewService().create_review(payload)


@router.post("/products/{product_id}/review-summary", response_model=ReviewSummary)
def summarize_reviews(product_id: int):
    return ReviewService().summarize_reviews(product_id)
