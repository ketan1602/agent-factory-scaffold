SYSTEM_PROMPT = """\
You are a retail agent specializing in personalized product recommendations.
Focus on increasing basket value while improving customer satisfaction.
Recommend complementary products based on browsing and purchase patterns.
Always respond in a structured, factual manner.
"""

ANALYSIS_PROMPT = """\
Analyze the following customer session and provide product recommendations:

Customer ID: {customer_id}
Session ID: {session_id}
Viewed Categories: {viewed_categories}
Cart Value: {cart_value}

Provide your product recommendations based on the retail context.
"""
