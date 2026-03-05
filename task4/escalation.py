"""
Task 4 — Escalation Decision Engine
Determines whether a customer interaction should be handled by AI or escalated to a human.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CustomerContext:
    """Customer context data (mirrors task3 structure)."""
    crm_data: Optional[dict] = None
    billing_data: Optional[dict] = None
    ticket_data: Optional[dict] = None
    data_complete: bool = True
    fetch_time_ms: float = 0.0


def should_escalate(
    context: CustomerContext,
    confidence_score: float,
    sentiment_score: float,
    intent: str,
) -> tuple:
    """
    Decide whether to escalate a customer interaction to a human agent.

    Rules (checked in order — first match wins):
      1. confidence < 0.65 → escalate ("low_confidence")
      2. sentiment < -0.6  → escalate ("angry_customer")
      3. same intent appears 3+ times in ticket history → escalate ("repeat_complaint")
      4. intent is "service_cancellation" → always escalate ("service_cancellation")
      5. customer is VIP AND billing is overdue → escalate ("vip_billing_issue")
      6. data_complete is False AND confidence < 0.80 → escalate ("incomplete_data")

    Returns:
        (bool, str): (should_escalate, reason)
    """

    # Rule 1 — Low confidence
    if confidence_score < 0.65:
        return (True, "low_confidence")

    # Rule 2 — Angry customer
    if sentiment_score < -0.6:
        return (True, "angry_customer")

    # Rule 3 — Repeat complaint (same intent 3+ times in ticket history)
    if context.ticket_data and "tickets" in context.ticket_data:
        intent_count = sum(
            1 for t in context.ticket_data["tickets"]
            if t.get("intent") == intent
        )
        if intent_count >= 3:
            return (True, "repeat_complaint")

    # Rule 4 — Service cancellation always escalates
    if intent == "service_cancellation":
        return (True, "service_cancellation")

    # Rule 5 — VIP with overdue billing
    is_vip = context.crm_data and context.crm_data.get("is_vip", False)
    is_overdue = context.billing_data and context.billing_data.get("payment_status") == "overdue"
    if is_vip and is_overdue:
        return (True, "vip_billing_issue")

    # Rule 6 — Incomplete data with less-than-high confidence
    if not context.data_complete and confidence_score < 0.80:
        return (True, "incomplete_data")

    # No escalation needed
    return (False, "no_escalation")
