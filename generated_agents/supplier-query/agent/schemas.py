from pydantic import BaseModel


class SupplierQueryInput(BaseModel):
    supplier_id: str
    query_type: str
    period: str
    metric: str


class SupplierQueryOutput(BaseModel):
    supplier_id: str
    response: str
    metric_value: float
    trend: str
    follow_up_needed: bool
