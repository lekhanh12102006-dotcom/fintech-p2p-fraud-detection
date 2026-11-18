
-- Part 1: Real-Time Feature Extraction Logic (Velocity & Balance Drain Signals)
WITH user_tx_history AS (
    SELECT 
        transaction_id,
        step AS hour_step,
        nameOrig AS sender_id,
        type AS tx_type,
        amount,
        oldbalanceOrg AS prev_balance,
        newbalanceOrig AS post_balance,
        isFraud,
        -- Calculate time gap (in hours) since the user's previous transaction
        step - LAG(step) OVER (PARTITION BY nameOrig ORDER BY step) AS hours_since_last_tx,
        -- Calculate cumulative amount transferred in the last 3 time steps
        SUM(amount) OVER (
            PARTITION BY nameOrig 
            ORDER BY step 
            RANGE BETWEEN 3 PRECEDING AND CURRENT ROW
        ) AS rolling_3h_volume,
        -- Ratio of current transfer amount to available balance
        CASE 
            WHEN oldbalanceOrg > 0 THEN ROUND(amount / oldbalanceOrg, 4)
            ELSE 0 
        END AS balance_drain_ratio
    FROM transactions
    WHERE type IN ('TRANSFER', 'CASH_OUT')
),

-- Part 2: Simulated Risk Scoring & Tier Routing
scored_transactions AS (
    SELECT 
        *,
        CASE 
            WHEN balance_drain_ratio >= 0.95 AND amount > 50000 THEN 85
            WHEN balance_drain_ratio >= 0.80 OR rolling_3h_volume > 100000 THEN 55
            ELSE 15
        END AS simulated_risk_score
    FROM user_tx_history
)

-- Part 3: Evaluate Tier Distribution, Recall, and User Friction Rate
SELECT 
    CASE 
        WHEN simulated_risk_score <= 30 THEN '1_LOW_RISK (AUTO_APPROVE)'
        WHEN simulated_risk_score <= 75 THEN '2_MEDIUM_RISK (STEP_UP_AUTH)'
        ELSE '3_HIGH_RISK (ON_HOLD_OPS)'
    END AS risk_tier,
    COUNT(*) AS total_transactions,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS traffic_share_pct,
    SUM(isFraud) AS fraud_cases_captured,
    ROUND(SUM(isFraud) * 100.0 / NULLIF(SUM(SUM(isFraud)) OVER (), 0), 2) AS fraud_recall_pct,
    -- False Positive Friction: Legitimate users pushed to Step-Up or Hold
    SUM(CASE WHEN isFraud = 0 AND simulated_risk_score > 30 THEN 1 ELSE 0 END) AS legitimate_users_impacted
FROM scored_transactions
GROUP BY 1
ORDER BY 1;
