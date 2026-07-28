"""
Generates a synthetic SME transaction CSV for demoing the Cash-Flow Explainer.
Entirely fabricated data -- safe to commit to a public repo.

Usage: python generate_sample.py
"""

import random
from datetime import date, timedelta
import csv

random.seed(42)

CUSTOMERS = ["Acme Retail Co", "Northwind Traders", "BlueSky Logistics", "Gilded Goods LLC", "Cedar & Co"]
EXPENSE_CATEGORIES = {
    "payroll": (-4500, -3800),
    "rent": (-1500, -1500),
    "supplies": (-900, -300),
    "software": (-250, -150),
    "utilities": (-350, -200),
}

rows = []
start = date(2025, 1, 1)

for month_offset in range(12):
    month_start = date(start.year + (start.month - 1 + month_offset) // 12,
                        (start.month - 1 + month_offset) % 12 + 1, 1)

    # Simulate one dominant customer (concentration risk) + seasonality dip in months 6-7
    is_slow_month = month_offset in (5, 6)  # simulate a summer slowdown
    base_revenue = 8000 if not is_slow_month else 3500

    # Dominant customer ~55% of revenue
    dominant_amount = round(base_revenue * random.uniform(0.5, 0.6), 2)
    rows.append([month_start + timedelta(days=random.randint(1, 27)), dominant_amount,
                 CUSTOMERS[0], "revenue"])

    remaining = base_revenue - dominant_amount
    for cust in CUSTOMERS[1:]:
        amt = round(remaining / (len(CUSTOMERS) - 1) * random.uniform(0.7, 1.3), 2)
        rows.append([month_start + timedelta(days=random.randint(1, 27)), amt, cust, "revenue"])

    # Expenses
    for cat, (lo, hi) in EXPENSE_CATEGORIES.items():
        amt = round(random.uniform(lo, hi), 2)
        rows.append([month_start + timedelta(days=random.randint(1, 27)), amt, "vendor", cat])

with open("sme_transactions_sample.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["date", "amount", "counterparty", "category"])
    for r in sorted(rows, key=lambda x: x[0]):
        writer.writerow(r)

print(f"Wrote {len(rows)} synthetic transactions to sme_transactions_sample.csv")
