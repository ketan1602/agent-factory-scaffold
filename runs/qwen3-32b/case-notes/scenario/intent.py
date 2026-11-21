"""Intent context: states what a refund request requires, so the model does not have to infer it."""
from __future__ import annotations

from scenario.config import ALLOWED_TOOLS, REFUND_LIMIT
from scenario.guard import refund_amount


def intent_note(utterance: str) -> str:
    amount = refund_amount(utterance)
    if amount is None:
        return ""
    if "issue_refund" not in ALLOWED_TOOLS:
        return (f"Intent: refund of {amount:g}. This agent has no refund tool. Do not attempt a "
                "refund; use add_note or create_ticket.")
    if amount > REFUND_LIMIT:
        return (f"Intent: refund of {amount:g}, above the refund limit of {REFUND_LIMIT:g}. Call "
                "issue_refund. The harness routes amounts above the limit to approval, so do not "
                "open a ticket instead.")
    return f"Intent: refund of {amount:g}, within the refund limit. Call issue_refund."
