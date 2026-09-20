from pydantic import BaseModel


class FraudFlagInput(BaseModel):
    transaction_id: str
    amount: float
    merchant_category: str
    is_online: bool
    customer_history_score: float


class FraudFlagOutput(BaseModel):
    transaction_id: str
    risk_level: str
    risk_score: float
    flags: list[str]
    action: str
