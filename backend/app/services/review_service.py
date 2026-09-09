from datetime import datetime, timezone

from fastapi import HTTPException
from openai import OpenAI

from app.core.config import settings
from app.db.mongo import mongo_db
from app.schemas.schemas import ReviewCreate


class ReviewService:
    def create_review(self, payload: ReviewCreate) -> dict:
        document = payload.model_dump()
        document["created_at"] = datetime.now(timezone.utc)
        result = mongo_db.reviews.insert_one(document)
        mongo_db.audit_events.insert_one(
            {
                "event_type": "review.created",
                "payload": {"product_id": payload.product_id, "review_id": str(result.inserted_id)},
                "created_at": datetime.now(timezone.utc),
            }
        )
        return {**payload.model_dump(), "id": str(result.inserted_id)}

    def list_reviews(self, product_id: int) -> list[dict]:
        reviews = []
        for doc in mongo_db.reviews.find({"product_id": product_id}).sort("created_at", -1):
            doc["id"] = str(doc.pop("_id"))
            doc.pop("created_at", None)
            reviews.append(doc)
        return reviews

    def summarize_reviews(self, product_id: int) -> dict:
        reviews = self.list_reviews(product_id)
        if not reviews:
            raise HTTPException(status_code=404, detail="No reviews found for this product")

        if not settings.openai_api_key:
            raise HTTPException(
                status_code=503,
                detail="ChatGPT Review Insights requires OPENAI_API_KEY; core retail features remain available without it.",
            )

        review_text = "\n\n".join(
            f"Rating: {r['rating']}/5\nTitle: {r['title']}\nReview: {r['body']}" for r in reviews[:50]
        )
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.responses.create(
            model=settings.openai_model,
            input=(
                "You are an ecommerce review analyst. Summarize the customer reviews below for a product manager. "
                "Return concise plain text with four sections: Executive summary, Common positives, Common concerns, "
                "and Recommended product actions. Do not invent facts beyond the supplied reviews.\n\n" + review_text
            ),
        )
        return {
            "product_id": product_id,
            "review_count": len(reviews),
            "summary": response.output_text,
        }
