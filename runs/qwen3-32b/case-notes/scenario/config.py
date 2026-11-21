"""Agent identity, tool grants and limits. Generated from manifests/case-notes.yaml; edit the manifest."""

AGENT_ID = "case-notes"
OWNER = "customer-operations"
SCOPE = "support"
ALLOWED_TOOLS = ("add_note", )
MAX_TOKENS = 2000
MAX_COST_USD = 0.1
REFUND_LIMIT = 100.0
APPROVERS = {"supervisor-1"}