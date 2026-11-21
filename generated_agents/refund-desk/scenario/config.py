"""Agent identity, tool grants and limits. Generated from manifests/refund-desk.yaml; edit the manifest."""

AGENT_ID = "refund-desk"
OWNER = "customer-operations"
SCOPE = "support"
ALLOWED_TOOLS = ("issue_refund", "add_note", )
MAX_TOKENS = 5000
MAX_COST_USD = 0.25
REFUND_LIMIT = 100.0
APPROVERS = {"supervisor-1"}