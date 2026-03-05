# ANSWERS.md — Task 5: Written Design Questions

---

## Q1: Partial Transcripts — Query on Partial or Wait?

I would use a **hybrid approach**: buffer partial transcripts and start lightweight pre-fetching, but don't trigger the main AI response until the speaker finishes.

Specifically, as partial transcripts arrive every 200ms, I'd run intent detection on the partial text. Once we get a high-confidence intent (e.g., "billing"), we can start pre-fetching the customer's billing records and account info from the database in the background. This way, by the time the customer finishes speaking, the data is already loaded.

However, I would **not** send partial text to the main LLM for generating a response — partial sentences are often misleading (e.g., "I want to cancel" might become "I want to cancel my add-on, not my plan"). Generating an AI response on incomplete input wastes API calls and could produce wrong answers.

The tradeoff is: pre-fetching costs extra database reads (some may be unnecessary if the intent changes), but it saves 200–400ms of latency when the customer finishes speaking. The risk is low because database reads are cheap and idempotent.

---

## Q2: Auto-Adding Resolutions to Knowledge Base — What Could Go Wrong?

**Problem 1: Outdated information accumulates.** Over 6 months, policies, pricing, and procedures change. A resolution that was correct in January ("your plan includes free roaming") may be wrong by June. The knowledge base keeps serving stale answers, and CSAT stays high because customers don't realize they got wrong info — until they do.

**Prevention:** Tag every knowledge base entry with a creation date and the policy version it references. Run a weekly automated check that flags entries older than 30 days for human review. Expire entries automatically after 90 days unless re-validated.

**Problem 2: Bias toward simple issues.** Easy problems (password resets, balance checks) get resolved quickly and receive high CSAT. Complex issues (billing disputes, outage complaints) rarely get CSAT ≥ 4. Over time, the knowledge base becomes full of simple answers and lacks coverage for hard problems, making the system worse at handling difficult cases.

**Prevention:** Track the distribution of intents in the knowledge base. Set a minimum coverage threshold per intent category. If complex intents fall below the threshold, manually curate and add entries for those categories regardless of CSAT.

---

## Q3: Customer Scenario — "4 Days Without Internet, 3 Calls, Want to Cancel"

**Step 1:** The AI detects multiple escalation signals — sentiment is very negative (the customer says "useless"), intent is "service_cancellation," and the ticket history shows 3+ prior calls about the same issue (repeat_complaint rule).

**Step 2:** The `should_escalate()` function triggers immediately with reason "service_cancellation" (Rule 4, which always escalates). The AI does not attempt to resolve this on its own.

**Step 3:** The AI responds empathetically but briefly: *"I completely understand your frustration — being without internet for 4 days is unacceptable, and I'm sorry we haven't fixed this yet. I'm connecting you right now to a senior specialist who can resolve this immediately."*

**Step 4:** The AI passes the following to the human agent: the full transcript, the customer's account info (pre-fetched), the 3 previous ticket IDs related to the outage, the negative sentiment score, and a recommended action of "retention offer + expedited repair." This gives the human agent everything they need without asking the customer to repeat themselves.

---

## Q4: Single Most Important Improvement

I would add a **real-time feedback loop that tracks resolution accuracy** — specifically, a system that compares the AI's suggested resolution against the actual outcome 24 hours later.

**How it works:** After every AI-handled interaction, the system schedules a follow-up check. Did the customer call back about the same issue? Did they give low CSAT? Did the agent who escalated need to completely redo the resolution? Each of these signals creates a "correction record" linked to the original AI response.

**How to build it:** Create a `resolution_tracking` table that stores the original AI response, the follow-up signals, and a computed accuracy score. A nightly batch job aggregates these into per-intent, per-prompt accuracy metrics. When accuracy drops below a threshold for a specific intent, the system automatically flags that intent for human review and optionally adjusts the confidence threshold for that intent type.

**How to measure:** Track two metrics: (1) **re-contact rate** — percentage of customers who call back within 48 hours about the same issue (should decrease), and (2) **first-contact resolution rate** — percentage of issues resolved without escalation or callback (should increase). Target: 10% improvement in first-contact resolution within 3 months.
