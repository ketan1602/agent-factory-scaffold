"""Agent identity, tool grants and limits. Generated from manifests/ticket-triage.yaml; edit the manifest."""

AGENT_ID = "ticket-triage"
OWNER = "customer-operations"
SCOPE = "support"
ALLOWED_TOOLS = ("create_ticket", "add_note", )
MAX_TOKENS = 5000
MAX_COST_USD = 0.25
REFUND_LIMIT = 100.0
APPROVERS = {"supervisor-1"}