import pandas as pd
import numpy as np
import duckdb
import matplotlib.pyplot as plt

# 1. Load PaySim Dataset
# Dataset source: Kaggle PaySim Mobile Money Simulator
DATA_PATH = "paysim dataset.csv"
df = pd.read_csv(DATA_PATH)

print(f"Total transactions loaded: {len(df):,}")
print(f"Overall fraud rate: {df['isFraud'].mean() * 100:.4f}%\n")

# 2. SQL Analysis via DuckDB: Fraud Distribution by Transaction Type
channel_query = """
SELECT 
    type AS transaction_type,
    COUNT(*) AS total_tx,
    SUM(isFraud) AS fraud_tx,
    ROUND(SUM(isFraud) * 100.0 / COUNT(*), 4) AS fraud_rate_pct,
    ROUND(AVG(amount), 2) AS avg_tx_amount
FROM df
GROUP BY type
ORDER BY fraud_tx DESC;
"""
channel_summary = duckdb.query(channel_query).to_df()
print("--- Fraud Distribution by Channel ---")
print(channel_summary.to_string(index=False))

# 3. Account Draining Pattern Analysis (TRANSFER & CASH_OUT only)
draining_query = """
WITH risky_channels AS (
    SELECT *
    FROM df
    WHERE type IN ('TRANSFER', 'CASH_OUT')
)
SELECT 
    isFraud,
    COUNT(*) AS tx_count,
    ROUND(AVG(amount), 2) AS avg_amount,
    ROUND(SUM(CASE WHEN newbalanceOrig = 0 AND oldbalanceOrg > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS account_drain_pct
FROM risky_channels
GROUP BY isFraud;
"""
draining_summary = duckdb.query(draining_query).to_df()
print("\n--- Account Draining Behavior (Legitimate vs Fraud) ---")
print(draining_summary.to_string(index=False))

# 4. Feature Engineering Preview: Balance Ratio & Anomaly Flag
df['amount_to_balance_ratio'] = np.where(
    df['oldbalanceOrg'] > 0,
    df['amount'] / df['oldbalanceOrg'],
    0
)

# 5. Visualization for Portfolio Documentation
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Chart 1: Fraud Count by Channel
axes[0].bar(channel_summary['transaction_type'], channel_summary['fraud_tx'], color='#d9534f')
axes[0].set_title('Fraudulent Transactions by Channel Type', fontsize=11, fontweight='bold')
axes[0].set_ylabel('Number of Fraud Cases')
axes[0].grid(axis='y', linestyle='--', alpha=0.5)

# Chart 2: Account Draining Rate (Legitimate vs Fraud)
labels = ['Legitimate (isFraud=0)', 'Fraudulent (isFraud=1)']
axes[1].bar(labels, draining_summary['account_drain_pct'], color=['#5bc0de', '#d9534f'], width=0.5)
axes[1].set_title('Percentage of Transactions Emptying 100% Balance', fontsize=11, fontweight='bold')
axes[1].set_ylabel('Account Drain Rate (%)')
axes[1].set_ylim(0, 100)
axes[1].grid(axis='y', linestyle='--', alpha=0.5)

plt.tight_layout()
plt.savefig('fraud_discovery_charts.png', dpi=300)
print("\nSaved visualization to fraud_discovery_charts.png")
