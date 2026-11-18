# Real-Time P2P Fraud Detection & AI Investigation Copilot

Project Context: Modeling real-world operational challenges at large-scale digital payment super-apps (such as MoMo and ZaloPay).
Role: Product / Risk Business Analyst (AI-Enabled BA)

---

## 1. Problem Statement & Motivation

In high-volume e-wallet platforms, the core challenge is not making peer-to-peer (P2P) transfers fast, but stopping fraudsters in real time without adding friction for legitimate users.

Currently, digital payment platforms face two critical bottlenecks:
1. High-velocity fraud attacks: Account Takeover (ATO) and Money Mule schemes typically execute and drain funds within 3 minutes. Manual review is too slow to prevent financial loss.
2. Fraud Operations overload: Thousands of flagged transactions pile up daily. A risk analyst spends an average of 5–7 minutes cross-referencing multiple database tables per case, delaying payouts for genuine customers.

Project Objective: Design an intelligent risk-routing workflow that combines real-time Machine Learning scoring (to filter threats instantly) with an LLM-powered AI Copilot (to summarize case context and accelerate manual investigations).

### Target Success Metrics (KPIs)
- Reduce total financial loss from P2P fraud by 40%.
- Maintain end-to-end scoring latency under 250ms to ensure a seamless checkout/transfer experience.
- Keep the false positive friction rate (legitimate users triggered for extra verification) below 1.5%.
- Cut Average Handling Time (AHT) for Fraud Ops analysts by 60% using automated AI case summaries.

---

## 2. Data Discovery & Key Insights
(Full SQL/Python analysis and cost-benefit models are available in /01_data_discovery)

Before drafting any requirements or wireframes, I analyzed the PaySim dataset (6.3 million simulated mobile money transactions) using SQL and Python to uncover actionable fraud patterns:

- Concentrated attack vectors: 100% of fraudulent activity occurs strictly within TRANSFER and CASH_OUT flows, while bill payments and cash-ins remain clean.
- Account draining behavior: 85.4% of fraudulent transactions follow a distinct pattern—immediately after a new device login or password reset, the account transfers 100% of its available balance (oldbalanceOrg - amount == 0).
- Cost-benefit threshold optimization: Financial modeling shows that missing one fraudulent transaction costs 25x more than the operational cost of triggering a biometric check for a legitimate user. Based on this trade-off, I established two optimal risk score cutoffs at 30 and 75.

---

## 3. System Workflow & Risk Routing

Instead of relying on rigid binary rules (block or allow), the system uses a three-tier routing engine driven by a real-time Risk Score (0–100):

| Risk Tier | Score Range | System Action | User & Operations Experience |
| :--- | :--- | :--- | :--- |
| Low Risk | 0 – 30 | Auto-Approve (AUTO_APPROVE) | Instant transfer completed in under 1 second with zero friction. |
| Medium Risk | 31 – 75 | Step-Up Auth (STEP_UP_AUTH) | Prompts user for biometric liveness verification matched against chip-based ID before releasing funds. |
| High Risk | 76 – 100 | Hold Transaction (ON_HOLD) | Funds are held for up to 30 minutes. A ticket with an AI Copilot summary is routed to Fraud Ops for review. |

### Edge Cases & System Resilience
In production Fintech systems, failures rarely happen on the happy path. I explicitly specified safeguards for critical technical edge cases:

- ML Timeout & Fallback Mechanism: If the ML scoring service takes longer than 250ms to respond, the core payment service bypasses the model and falls back to a deterministic Rule Engine (e.g., triggering biometric verification for transfers over 10M VND on unrecognized devices) so users never experience app freezes.
- Idempotency Control: Every transfer request carries a unique Idempotency-Key in the header. If a user taps "Confirm" multiple times due to an unstable network, the system guarantees the transaction is scored and debited strictly once.
- AI Guardrails & PII Masking: Before sending transaction context to an external LLM API to generate Ops summaries, a middleware layer masks all Personally Identifiable Information (full name, national ID, phone number), transmitting only anonymized hashes and behavioral risk signals.

---

## 4. Repository Structure

Each folder represents a distinct phase of the end-to-end product development lifecycle:

- 01_data_discovery/: Python and SQL scripts analyzing 6.3M transactions, fraud pattern visualizations, and risk threshold calculations.
- 02_product_and_system_specs/: Product Requirements Document (PRD), User Stories (Given-When-Then), edge-case matrices, and system Sequence Diagrams.
- 03_ai_copilot_and_api/: REST API specifications (JSON Request/Response payloads) connecting Core Payment, ML Scoring, and AI Copilot, along with PII masking rules.
- 04_wireframes_and_metrics/: Figma wireframe links (user step-up auth flow and internal Fraud Ops portal) and the post-launch event tracking plan.

---

## 5. Skills & Tools Demonstrated
- Product & System Analysis: PRD/SRS Documentation, User Stories (Given-When-Then), BPMN 2.0, Sequence Diagrams, REST/JSON API Mapping, Fallback & Edge-Case Design.
- Data & AI Integration: SQL (CTEs, Window Functions), Python (pandas, numpy), Cost-Benefit Threshold Modeling, LLM Prompt Engineering & PII Guardrails.
- UX & Product Analytics: Figma (Wireframing), Event Tracking Plans, KPI Definition & A/B Testing Frameworks.
