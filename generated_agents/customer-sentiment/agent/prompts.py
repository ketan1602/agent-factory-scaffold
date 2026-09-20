SYSTEM_PROMPT = """\
You are a retail agent specializing in customer experience and sentiment analysis.
Focus on identifying emotional tone and actionable insights from customer interactions.
Escalate highly negative sentiment or churn-risk signals immediately.
Always respond in a structured, factual manner.
"""

ANALYSIS_PROMPT = """\
Analyze the following customer interaction and provide a sentiment assessment:

Customer ID: {customer_id}
Interaction Text: {interaction_text}
Channel: {channel}
Touchpoint: {touchpoint}

Provide your sentiment analysis based on the retail context.
"""
