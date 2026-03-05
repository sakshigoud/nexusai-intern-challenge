"""
Tests for Task 4 — Escalation Decision Engine.
Run with: pytest task4/ -v
"""

from escalation import should_escalate, CustomerContext


def _make_context(
    is_vip=False,
    payment_status="current",
    tickets=None,
    data_complete=True,
):
    """Helper to build a CustomerContext for testing."""
    return CustomerContext(
        crm_data={"name": "Test User", "is_vip": is_vip},
        billing_data={"payment_status": payment_status},
        ticket_data={"tickets": tickets or []},
        data_complete=data_complete,
    )


# --- One test per rule ------------------------------------------------

def test_rule1_low_confidence():
    """Low confidence (< 0.65) should trigger escalation.
    This matters because unreliable AI responses should not reach the customer."""
    ctx = _make_context()
    result, reason = should_escalate(ctx, confidence_score=0.5, sentiment_score=0.0, intent="billing_dispute")
    assert result is True
    assert reason == "low_confidence"


def test_rule2_angry_customer():
    """Very negative sentiment (< -0.6) should trigger escalation.
    Angry customers need human empathy, not automated replies."""
    ctx = _make_context()
    result, reason = should_escalate(ctx, confidence_score=0.9, sentiment_score=-0.8, intent="billing_dispute")
    assert result is True
    assert reason == "angry_customer"


def test_rule3_repeat_complaint():
    """If the same intent appears 3+ times in ticket history, escalate.
    Repeat issues mean the AI has failed to resolve the problem."""
    tickets = [
        {"intent": "service_outage", "status": "closed"},
        {"intent": "service_outage", "status": "closed"},
        {"intent": "service_outage", "status": "open"},
    ]
    ctx = _make_context(tickets=tickets)
    result, reason = should_escalate(ctx, confidence_score=0.9, sentiment_score=0.0, intent="service_outage")
    assert result is True
    assert reason == "repeat_complaint"


def test_rule4_service_cancellation():
    """Service cancellation intent should always escalate — no exceptions.
    Losing a customer is high-stakes; a human must handle it."""
    ctx = _make_context()
    result, reason = should_escalate(ctx, confidence_score=0.99, sentiment_score=0.5, intent="service_cancellation")
    assert result is True
    assert reason == "service_cancellation"


def test_rule5_vip_billing_overdue():
    """VIP customer with overdue billing should escalate.
    VIPs generate more revenue, so overdue billing needs urgent human attention."""
    ctx = _make_context(is_vip=True, payment_status="overdue")
    result, reason = should_escalate(ctx, confidence_score=0.9, sentiment_score=0.0, intent="plan_upgrade")
    assert result is True
    assert reason == "vip_billing_issue"


def test_rule6_incomplete_data_low_confidence():
    """Incomplete data with confidence < 0.80 should escalate.
    Missing context + mediocre confidence is too risky for AI-only handling."""
    ctx = _make_context(data_complete=False)
    result, reason = should_escalate(ctx, confidence_score=0.75, sentiment_score=0.0, intent="billing_dispute")
    assert result is True
    assert reason == "incomplete_data"


# --- Edge case tests --------------------------------------------------

def test_edge_no_escalation_when_all_clear():
    """High confidence, positive sentiment, no repeat issues, non-critical intent,
    complete data, and non-VIP — AI should handle this without escalation."""
    ctx = _make_context()
    result, reason = should_escalate(ctx, confidence_score=0.9, sentiment_score=0.3, intent="plan_upgrade")
    assert result is False
    assert reason == "no_escalation"


def test_edge_cancellation_overrides_high_confidence():
    """Even with confidence 0.99 and positive sentiment, service_cancellation
    must still escalate. This tests that Rule 4 cannot be bypassed by other signals.
    In our implementation, rules are checked in order and service_cancellation (Rule 4)
    fires before the 'no escalation' default."""
    ctx = _make_context()
    result, reason = should_escalate(ctx, confidence_score=0.99, sentiment_score=0.9, intent="service_cancellation")
    assert result is True
    assert reason == "service_cancellation"
