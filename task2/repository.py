"""
Task 2 — CallRecordRepository
Python class to read/write call records using asyncpg.
"""

import asyncpg
import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()  # Load .env file from project root


class CallRecordRepository:
    """Repository for call_records table using asyncpg."""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    @classmethod
    async def create(cls, dsn: str = None):
        """Factory method to create repository with a connection pool."""
        dsn = dsn or os.getenv("DATABASE_URL", "postgresql://localhost/nexusai")
        pool = await asyncpg.create_pool(dsn)
        return cls(pool)

    async def save(self, call_data: dict) -> int:
        """
        Insert a new call record.

        Args:
            call_data: Dictionary with keys matching call_records columns.

        Returns:
            The id of the newly inserted record.
        """
        query = """
            INSERT INTO call_records
                (customer_phone, channel, transcript, ai_response, intent,
                 outcome, confidence_score, csat_score, duration_seconds)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                call_data["customer_phone"],
                call_data["channel"],
                call_data["transcript"],
                call_data.get("ai_response"),
                call_data.get("intent"),
                call_data["outcome"],
                call_data["confidence_score"],
                call_data.get("csat_score"),
                call_data.get("duration_seconds", 0),
            )
            return row["id"]

    async def get_recent(self, phone: str, limit: int = 5) -> list:
        """
        Get the most recent call records for a phone number.

        Args:
            phone: Customer phone number.
            limit: Max records to return (default 5).

        Returns:
            List of dicts representing call records.
        """
        query = """
            SELECT * FROM call_records
            WHERE customer_phone = $1
            ORDER BY created_at DESC
            LIMIT $2
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, phone, limit)
            return [dict(row) for row in rows]

    async def get_low_resolution_intents(self, days: int = 7) -> list:
        """
        Get top 5 intent types with the lowest resolution rate
        in the last N days, along with their average CSAT.

        Returns:
            List of dicts with intent, total_calls, resolved_count,
            resolution_rate, and avg_csat.
        """
        query = """
            SELECT
                intent,
                COUNT(*)                                            AS total_calls,
                COUNT(*) FILTER (WHERE outcome = 'resolved')        AS resolved_count,
                ROUND(
                    COUNT(*) FILTER (WHERE outcome = 'resolved')::numeric
                    / COUNT(*), 2
                )                                                   AS resolution_rate,
                ROUND(AVG(csat_score)::numeric, 2)                  AS avg_csat
            FROM call_records
            WHERE created_at >= NOW() - INTERVAL '1 day' * $1
              AND intent IS NOT NULL
            GROUP BY intent
            ORDER BY resolution_rate ASC
            LIMIT 5
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, days)
            return [dict(row) for row in rows]
