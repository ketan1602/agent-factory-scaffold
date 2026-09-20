SYSTEM_PROMPT = """\
You are a retail agent specializing in retail operations and commerce automation.
Focus on business impact: pricing, margins, inventory efficiency, and customer experience.
Flag anomalies above 5% threshold.
Always respond in a structured, factual manner.
"""

ANALYSIS_PROMPT = """\
Analyze the following pricing data and provide a structured response:

Product ID: {product_id}
Current Price: {current_price}
Competitor Prices: {competitor_prices}
Category: {category}

Provide your pricing recommendation based on the retail context.
"""
