# Edge Cases, Failure Modes & Fallback Rules

## 1. System Resilience & Failure Handling Matrix

| Scenario ID | Failure / Edge Case | Business & Technical Risk | Deterministic Fallback / System Rule |
| :--- | :--- | :--- | :--- |
| EC-01 | ML Scoring Service Timeout (> 250ms) or HTTP 5xx Error | Payment checkout freezes, causing severe user drop-off and revenue loss. | Bypass ML model immediately and execute the local Deterministic Rule Engine (see Section 2) within 20ms. Log event as `SCORING_FALLBACK`. |
| EC-02 | Duplicate Transfer Requests (Network Lag / Double Tap) | User taps "Confirm" twice within 500ms, causing duplicate balance deductions or conflicting risk scores. | Enforce strict `Idempotency-Key` validation at the API Gateway. Return the cached response of the first request for any duplicate key within a 24-hour window. |
| EC-03 | Fraud Ops SLA Breach (Ticket Unreviewed > 30 Mins) | Legitimate user's funds remain frozen indefinitely, violating customer service SLAs. | Trigger an automated cron job at minute 30: auto-cancel the transaction (`EXPIRED_HOLD`), release reserved funds back to sender's available balance, and notify user to retry. |
| EC-04 | LLM Copilot API Outage or High Latency (> 3s) | Ops Portal fails to load the investigation ticket, blocking analysts from reviewing held funds. | Render the raw structured risk indicators (feature table) immediately without waiting for the LLM text summary; display banner: "AI Summary temporarily unavailable." |
| EC-05 | Concurrent Balance Drain (Race Condition) | Two transfer requests initiated simultaneously from different sessions against the same balance. | Apply pessimistic row-level locking (`SELECT ... FOR UPDATE`) on the sender's wallet ledger during balance reservation. |

---

## 2. Deterministic Rule Engine (Fallback Rules)

When the ML Scoring Service is unavailable (EC-01), the Core Payment Service evaluates the following sequential rules:

1. Rule R-01 (High-Value New Device):
   - Condition: `is_new_device == TRUE` AND `amount >= 10,000,000 VND`
   - Action: Route to `ON_HOLD` (High Risk).
2. Rule R-02 (Account Drain Threshold):
   - Condition: `(amount / available_balance) >= 0.90` AND `amount >= 5,000,000 VND`
   - Action: Route to `STEP_UP_AUTH` (Require Biometric Liveness Check).
3. Rule R-03 (High Velocity Burst):
   - Condition: `outbound_tx_count_last_10m >= 4`
   - Action: Route to `STEP_UP_AUTH`.
4. Rule R-04 (Default Safe Pass):
   - Condition: None of the above rules match.
   - Action: Route to `AUTO_APPROVE` (Low Risk).

---

## 3. Transaction State Lifecycle

Every P2P transfer must follow strict state transitions:
- `INITIATED` -> `SCORING` -> `AUTO_APPROVED` -> `SETTLED`
- `INITIATED` -> `SCORING` -> `PENDING_STEP_UP` -> `SETTLED` (or `FAILED_AUTH`)
- `INITIATED` -> `SCORING` -> `ON_HOLD` -> `OPS_APPROVED` -> `SETTLED`
- `INITIATED` -> `SCORING` -> `ON_HOLD` -> `OPS_REJECTED` / `EXPIRED_HOLD` -> `REVERSED`
