"""Agent identity, tool grants and limits. Generated from manifests/support-agent.yaml; edit the manifest."""

AGENT_ID = "support-agent"
OWNER = "customer-platform"
SCOPE = "support"
ALLOWED_TOOLS = ("create_ticket", "add_note", "issue_refund", )
MAX_TOKENS = 5000
MAX_COST_USD = 0.25
REFUND_LIMIT = 100.0
APPROVERS = {"supervisor-1"}