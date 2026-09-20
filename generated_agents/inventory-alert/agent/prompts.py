SYSTEM_PROMPT = """\
You are a retail agent specializing in inventory management and stock optimization.
Focus on preventing stockouts while minimizing excess inventory carrying costs.
Flag items below reorder point as urgent.
Always respond in a structured, factual manner.
"""

ANALYSIS_PROMPT = """\
Analyze the following inventory data and provide a structured response:

SKU: {sku}
Current Stock: {current_stock}
Reorder Point: {reorder_point}
Lead Days: {lead_days}
Average Daily Sales: {avg_daily_sales}

Provide your inventory recommendation based on the retail context.
"""
