from pydantic import BaseModel


class InventoryAlertInput(BaseModel):
    sku: str
    current_stock: int
    reorder_point: int
    lead_days: int
    avg_daily_sales: float


class InventoryAlertOutput(BaseModel):
    sku: str
    alert_level: str
    recommended_order_qty: int
    days_until_stockout: int
    message: str
