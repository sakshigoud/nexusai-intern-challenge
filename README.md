# NexusAI Intern Challenge

## Project Structure

```
nexusai/
├── ANSWERS.md              # Task 5 — Written design questions
├── README.md               # This file
├── requirements.txt        # Python dependencies
├── task1/
│   └── handler.py          # Async AI message handler
├── task2/
│   ├── schema.sql          # PostgreSQL table + indexes
│   └── repository.py       # CallRecordRepository class
├── task3/
│   └── fetcher.py          # Parallel data fetcher demo
└── task4/
    ├── escalation.py       # Escalation decision engine
    └── test_escalation.py  # 8 pytest test cases
```

## Setup

```bash
pip install -r requirements.txt
```

## How to Run Each Task

### Task 1 — AI Message Handler

Requires an `OPENAI_API_KEY` environment variable.

```bash
set OPENAI_API_KEY=your_key_here
python task1/handler.py
```

### Task 2 — Database Schema

1. Create the table in PostgreSQL:
   ```bash
   psql -d your_database -f task2/schema.sql
   ```
2. The `CallRecordRepository` class in `task2/repository.py` connects via the `DATABASE_URL` environment variable (defaults to `postgresql://localhost/nexusai`).

### Task 3 — Parallel Data Fetcher

No external dependencies needed — uses mock data with simulated delays.

```bash
python task3/fetcher.py
```

**Sample timing output:**

```
==================================================
Sequential Fetch
==================================================
  Time: 702.45 ms
  Data complete: True

==================================================
Parallel Fetch
==================================================
  Time: 387.12 ms
  Data complete: True

Speedup: 1.81x
```

The parallel version consistently achieves **~2x speedup** because all three requests run concurrently. Sequential time ≈ sum of all delays (~650–1050ms); parallel time ≈ the longest single delay (~200–400ms).

### Task 4 — Escalation Decision Engine

Run all 8 tests:

```bash
pytest task4/ -v
```

**Rule Conflict Explanation:**

When two rules could both apply, our engine checks rules in a **fixed priority order** (Rule 1 → Rule 6). The first matching rule wins. For example, if confidence is 0.90 but intent is `service_cancellation`, Rule 1 (low confidence) does NOT fire because 0.90 ≥ 0.65. Rule 4 (service cancellation) fires and returns `"service_cancellation"` as the reason. This priority-based approach is intentional — we check the *most dangerous* signals first (low confidence, angry customer) before checking business-logic rules (cancellation, VIP status). This means a truly unreliable AI response always gets escalated before we even consider the intent.

### Task 5 — Written Design Questions

See [ANSWERS.md](ANSWERS.md) for all four written responses.
