from pydantic import BaseModel


class CustomerSentimentInput(BaseModel):
    customer_id: str
    interaction_text: str
    channel: str
    touchpoint: str


class CustomerSentimentOutput(BaseModel):
    customer_id: str
    sentiment: str
    score: float
    action_recommended: str
    priority: str
