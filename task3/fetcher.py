"""
Task 3 — Parallel Data Fetcher
Demonstrates async parallelism by fetching data from multiple mock systems.
"""

import asyncio
import random
import time
import logging
from dataclasses import dataclass, field
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CustomerContext:
    """Merged result from all data sources."""
    crm_data: Optional[dict] = None
    billing_data: Optional[dict] = None
    ticket_data: Optional[dict] = None
    data_complete: bool = True
    fetch_time_ms: float = 0.0


# ─── Mock fetch functions ──────────────────────────────────────

async def fetch_crm(phone: str) -> dict:
    """Simulate CRM fetch (200–400ms delay)."""
    await asyncio.sleep(random.uniform(0.2, 0.4))
    return {
        "phone": phone,
        "name": "John Doe",
        "account_id": "ACC-10234",
        "plan": "Premium 5G",
        "is_vip": random.choice([True, False]),
        "member_since": "2021-03-15",
    }


async def fetch_billing(phone: str) -> dict:
    """Simulate billing fetch (150–350ms delay) with 10% failure chance."""
    await asyncio.sleep(random.uniform(0.15, 0.35))

    # 10% chance of timeout
    if random.random() < 0.10:
        raise TimeoutError("Billing system timed out")

    return {
        "phone": phone,
        "balance_due": 49.99,
        "last_payment": "2025-02-20",
        "payment_status": random.choice(["current", "overdue"]),
        "auto_pay": True,
    }


async def fetch_tickets(phone: str) -> dict:
    """Simulate ticket history fetch (100–300ms delay)."""
    await asyncio.sleep(random.uniform(0.1, 0.3))
    sample_intents = ["billing_dispute", "service_outage", "plan_upgrade",
                      "service_cancellation", "sim_issue"]
    return {
        "phone": phone,
        "tickets": [
            {"id": f"TK-{1000+i}", "intent": random.choice(sample_intents),
             "status": random.choice(["open", "closed"]), "date": f"2025-02-{20+i}"}
            for i in range(5)
        ],
    }


# ─── Sequential vs Parallel fetchers ──────────────────────────

async def fetch_sequential(phone: str) -> CustomerContext:
    """Fetch all data sources one after another."""
    start = time.perf_counter()

    crm = await fetch_crm(phone)

    try:
        billing = await fetch_billing(phone)
    except TimeoutError:
        logger.warning("Billing fetch failed (sequential) — returning None")
        billing = None

    tickets = await fetch_tickets(phone)

    elapsed = (time.perf_counter() - start) * 1000
    data_complete = all(v is not None for v in [crm, billing, tickets])

    return CustomerContext(
        crm_data=crm,
        billing_data=billing,
        ticket_data=tickets,
        data_complete=data_complete,
        fetch_time_ms=round(elapsed, 2),
    )


async def fetch_parallel(phone: str) -> CustomerContext:
    """Fetch all data sources in parallel using asyncio.gather."""
    start = time.perf_counter()

    results = await asyncio.gather(
        fetch_crm(phone),
        fetch_billing(phone),
        fetch_tickets(phone),
        return_exceptions=True,
    )

    crm, billing, tickets = results

    # Handle any exceptions in the results
    if isinstance(crm, Exception):
        logger.warning(f"CRM fetch failed: {crm}")
        crm = None
    if isinstance(billing, Exception):
        logger.warning(f"Billing fetch failed: {billing}")
        billing = None
    if isinstance(tickets, Exception):
        logger.warning(f"Tickets fetch failed: {tickets}")
        tickets = None

    elapsed = (time.perf_counter() - start) * 1000
    data_complete = all(v is not None for v in [crm, billing, tickets])

    return CustomerContext(
        crm_data=crm,
        billing_data=billing,
        ticket_data=tickets,
        data_complete=data_complete,
        fetch_time_ms=round(elapsed, 2),
    )


# ─── Demo / Timing comparison ─────────────────────────────────

async def main():
    phone = "+1-555-0100"

    print("=" * 50)
    print("Sequential Fetch")
    print("=" * 50)
    seq = await fetch_sequential(phone)
    print(f"  Time: {seq.fetch_time_ms:.2f} ms")
    print(f"  Data complete: {seq.data_complete}")

    print()

    print("=" * 50)
    print("Parallel Fetch")
    print("=" * 50)
    par = await fetch_parallel(phone)
    print(f"  Time: {par.fetch_time_ms:.2f} ms")
    print(f"  Data complete: {par.data_complete}")

    print()
    if seq.fetch_time_ms > 0 and par.fetch_time_ms > 0:
        speedup = seq.fetch_time_ms / par.fetch_time_ms
        print(f"Speedup: {speedup:.2f}x")


if __name__ == "__main__":
    asyncio.run(main())
