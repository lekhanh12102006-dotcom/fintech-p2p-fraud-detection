# System Sequence Diagram: Real-Time Fraud Scoring & Routing

The diagram below illustrates the end-to-end synchronous and asynchronous interactions across the Mobile App, Core Payment Service, ML Scoring Engine, Fallback Rule Engine, and AI Ops Copilot.

```mermaid
sequenceDiagram
    autonumber
    actor User as E-Wallet User
    participant App as Mobile App
    participant Core as Core Payment Service
    participant ML as ML Scoring Engine
    participant Rules as Fallback Rule Engine
    participant AI as AI Copilot (LLM)
    actor Ops as Fraud Ops Analyst

    User->>App: Confirm P2P Transfer (Amount, Recipient)
    App->>Core: POST /v1/transfers (Header: Idempotency-Key)
    
    Note over Core: Validate Idempotency-Key & Lock Balance

    Core->>ML: Request Risk Score (Timeout = 250ms)
    
    alt ML Responds Within 250ms
        ML-->>Core: Return Risk Score (0-100) + Top Risk Factors
    else ML Timeout (> 250ms) or Service Error
        Core->>Rules: Trigger Deterministic Fallback Rules
        Rules-->>Core: Return Fallback Tier Action
    end

    alt Score 0 - 30 (Low Risk)
        Core->>Core: Set Status = SETTLED & Credit Recipient
        Core-->>App: 200 OK (Transfer Successful)
        App-->>User: Show Success Receipt
    else Score 31 - 75 (Medium Risk)
        Core-->>App: 202 Accepted (Action: STEP_UP_AUTH)
        App-->>User: Prompt Biometric Liveness Check
        User->>App: Complete Face Scan
        App->>Core: POST /v1/transfers/{id}/verify-biometric
        Core->>Core: Verify & Settle Funds
        Core-->>App: 200 OK (Transfer Successful)
    else Score 76 - 100 (High Risk)
        Core->>Core: Set Status = ON_HOLD (Max 30m)
        Core-->>App: 202 Accepted (Status: Under Security Review)
        App-->>User: Show Pending Review Notice
        
        par Async Ops Escalation
            Core->>AI: Send Masked Transaction Context (PII Removed)
            AI-->>Core: Return 3-Bullet Risk Summary
            Core->>Ops: Push Alert Ticket + AI Summary to Portal
        end
        
        Ops->>Core: Submit Manual Decision (Approve / Reject + Reason)
        Note over Core: Write Immutable Record to Audit_Logs
    end
