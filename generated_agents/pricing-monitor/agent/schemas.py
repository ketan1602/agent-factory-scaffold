from pydantic import BaseModel


class PricingMonitorInput(BaseModel):
    product_id: str
    current_price: float
    competitor_prices: list[float]
    category: str


class PricingMonitorOutput(BaseModel):
    product_id: str
    recommendation: str
    suggested_price: float
    price_change_pct: float
    reasoning: str
