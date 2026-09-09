from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.postgres import get_db
from app.schemas.schemas import (
    CustomerCreate,
    CustomerRead,
    InventoryRead,
    OrderCreate,
    OrderRead,
    ProductCreate,
    ProductRead,
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


@router.post("/customers", response_model=CustomerRead, status_code=201)
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db)):
    return RetailService(db).create_customer(payload)


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


@router.get("/products/{product_id}/reviews", response_model=list[ReviewRead])
def list_reviews(product_id: int):
    return ReviewService().list_reviews(product_id)


@router.post("/reviews", response_model=ReviewRead, status_code=201)
def create_review(payload: ReviewCreate):
    return ReviewService().create_review(payload)


@router.post("/products/{product_id}/review-summary", response_model=ReviewSummary)
def summarize_reviews(product_id: int):
    return ReviewService().summarize_reviews(product_id)
