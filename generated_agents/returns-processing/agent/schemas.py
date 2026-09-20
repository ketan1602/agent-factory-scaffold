from pydantic import BaseModel


class ReturnsProcessingInput(BaseModel):
    order_id: str
    customer_id: str
    item_count: int
    total_value: float
    reason: str


class ReturnsProcessingOutput(BaseModel):
    order_id: str
    decision: str
    refund_amount: float
    processing_days: int
    instructions: str
