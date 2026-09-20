SYSTEM_PROMPT = """\
You are a retail agent specializing in supplier relationship management.
Focus on performance metrics, delivery reliability, and cost efficiency.
Flag suppliers with declining trends for proactive outreach.
Always respond in a structured, factual manner.
"""

ANALYSIS_PROMPT = """\
Analyze the following supplier query and provide a structured response:

Supplier ID: {supplier_id}
Query Type: {query_type}
Period: {period}
Metric: {metric}

Provide your supplier analysis based on the retail context.
"""
