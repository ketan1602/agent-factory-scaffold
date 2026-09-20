from pydantic import BaseModel


class DeliveryExceptionInput(BaseModel):
    shipment_id: str
    exception_type: str
    current_location: str
    original_eta: str
    delay_hours: int


class DeliveryExceptionOutput(BaseModel):
    shipment_id: str
    resolution: str
    revised_eta: str
    customer_notification: str
    escalate: bool
