from pydantic import BaseModel


class ProductRecommendationInput(BaseModel):
    customer_id: str
    session_id: str
    viewed_categories: list[str]
    cart_value: float


class ProductRecommendationOutput(BaseModel):
    customer_id: str
    recommendations: list[str]
    confidence_scores: list[float]
    reasoning: str
