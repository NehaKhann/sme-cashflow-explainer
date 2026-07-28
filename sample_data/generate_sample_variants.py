"""
Generates a folder of sample transaction CSVs, each engineered to demonstrate
a different, clearly recognizable risk scenario. Useful for demos: pick a
file, upload it, and the memo should show the corresponding risk flags.

All data is entirely synthetic -- safe to commit and share publicly.

Usage: python3 generate_sample_variants.py
Writes files into ./scenarios/
"""

import csv
import os
import random
from datetime import date, timedelta

OUT_DIR = "scenarios"
os.makedirs(OUT_DIR, exist_ok=True)


def write_csv(filename, rows):
    path = os.path.join(OUT_DIR, filename)
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "amount", "counterparty", "category"])
        for r in sorted(rows, key=lambda x: x[0]):
            writer.writerow(r)
    print(f"  wrote {path}  ({len(rows)} rows)")


def month_start(base: date, offset: int) -> date:
    y = base.year + (base.month - 1 + offset) // 12
    m = (base.month - 1 + offset) % 12 + 1
    return date(y, m, 1)


def rand_day(month_start_date: date) -> date:
    return month_start_date + timedelta(days=random.randint(1, 27))


BASE = date(2025, 1, 1)


# ---------------------------------------------------------------------------
# Scenario 1: Healthy, stable business -- should score LOW risk, no major flags
# ---------------------------------------------------------------------------
def scenario_healthy():
    random.seed(1)
    customers = ["Riverbend Cafe", "Oakview Supplies", "Maple & Co", "Sterling Retail", "Union Hardware"]
    rows = []
    for m in range(12):
        ms = month_start(BASE, m)
        monthly_revenue = random.uniform(9000, 9800)  # low volatility on purpose
        share_left = monthly_revenue
        for i, cust in enumerate(customers):
            share = monthly_revenue / len(customers) * random.uniform(0.85, 1.15)
            rows.append([rand_day(ms), round(share, 2), cust, "revenue"])
        for cat, (lo, hi) in {
            "payroll": (-4200, -3900), "rent": (-1400, -1400),
            "supplies": (-500, -300), "software": (-180, -120), "utilities": (-300, -200),
        }.items():
            rows.append([rand_day(ms), round(random.uniform(lo, hi), 2), "vendor", cat])
    write_csv("01_healthy_stable_business.csv", rows)


# ---------------------------------------------------------------------------
# Scenario 2: Severe customer concentration -- one client is ~75% of revenue
# ---------------------------------------------------------------------------
def scenario_concentration_risk():
    random.seed(2)
    dominant = "MegaClient Corp"
    others = ["Small Buyer A", "Small Buyer B", "Small Buyer C"]
    rows = []
    for m in range(12):
        ms = month_start(BASE, m)
        total = random.uniform(9000, 11000)
        dominant_amt = total * random.uniform(0.72, 0.78)
        rows.append([rand_day(ms), round(dominant_amt, 2), dominant, "revenue"])
        remaining = total - dominant_amt
        for cust in others:
            rows.append([rand_day(ms), round(remaining / len(others) * random.uniform(0.7, 1.3), 2), cust, "revenue"])
        for cat, (lo, hi) in {"payroll": (-4000, -3600), "rent": (-1300, -1300), "supplies": (-400, -200)}.items():
            rows.append([rand_day(ms), round(random.uniform(lo, hi), 2), "vendor", cat])
    write_csv("02_severe_customer_concentration.csv", rows)


# ---------------------------------------------------------------------------
# Scenario 3: Sustained negative cash flow -- 4+ consecutive losing months
# ---------------------------------------------------------------------------
def scenario_negative_cash_flow():
    random.seed(3)
    customers = ["Downtown Retail", "Corner Shop LLC", "Bright Goods"]
    rows = []
    for m in range(12):
        ms = month_start(BASE, m)
        # months 5-9 (0-indexed 4-8): revenue craters while expenses stay fixed
        is_bad_stretch = 4 <= m <= 8
        total_rev = random.uniform(4000, 5000) if is_bad_stretch else random.uniform(8500, 9500)
        for cust in customers:
            rows.append([rand_day(ms), round(total_rev / len(customers) * random.uniform(0.8, 1.2), 2), cust, "revenue"])
        for cat, (lo, hi) in {
            "payroll": (-5200, -4900), "rent": (-1600, -1600), "supplies": (-600, -400),
        }.items():
            rows.append([rand_day(ms), round(random.uniform(lo, hi), 2), "vendor", cat])
    write_csv("03_sustained_negative_cash_flow.csv", rows)


# ---------------------------------------------------------------------------
# Scenario 4: Sharp single-month revenue drop (e.g. lost a major contract)
# ---------------------------------------------------------------------------
def scenario_sharp_drop():
    random.seed(4)
    customers = ["Anchor Client Inc", "Steady Buyer", "Regular Co"]
    rows = []
    for m in range(12):
        ms = month_start(BASE, m)
        # month index 7 (August) drops ~65% vs normal
        total_rev = random.uniform(9500, 10500) if m != 7 else random.uniform(3200, 3600)
        for cust in customers:
            rows.append([rand_day(ms), round(total_rev / len(customers) * random.uniform(0.85, 1.15), 2), cust, "revenue"])
        for cat, (lo, hi) in {"payroll": (-4500, -4200), "rent": (-1500, -1500), "supplies": (-450, -250)}.items():
            rows.append([rand_day(ms), round(random.uniform(lo, hi), 2), "vendor", cat])
    write_csv("04_sharp_single_month_drop.csv", rows)


# ---------------------------------------------------------------------------
# Scenario 5: High revenue volatility, no single dominant cause -- erratic month to month
# ---------------------------------------------------------------------------
def scenario_high_volatility():
    random.seed(5)
    customers = ["Variable Ventures", "Irregular Imports", "Patchy Retail", "Uneven Supply Co"]
    rows = []
    for m in range(12):
        ms = month_start(BASE, m)
        total_rev = random.uniform(3000, 14000)  # wide swings every month
        for cust in customers:
            rows.append([rand_day(ms), round(total_rev / len(customers) * random.uniform(0.6, 1.4), 2), cust, "revenue"])
        for cat, (lo, hi) in {"payroll": (-4000, -3700), "rent": (-1200, -1200), "supplies": (-500, -200)}.items():
            rows.append([rand_day(ms), round(random.uniform(lo, hi), 2), "vendor", cat])
    write_csv("05_high_revenue_volatility.csv", rows)


# ---------------------------------------------------------------------------
# Scenario 6: Thin customer base -- only 2 customers total, both moderate share
# ---------------------------------------------------------------------------
def scenario_thin_customer_base():
    random.seed(6)
    customers = ["Client Alpha", "Client Beta"]
    rows = []
    for m in range(12):
        ms = month_start(BASE, m)
        total_rev = random.uniform(8000, 9500)
        for cust in customers:
            rows.append([rand_day(ms), round(total_rev / len(customers) * random.uniform(0.9, 1.1), 2), cust, "revenue"])
        for cat, (lo, hi) in {"payroll": (-3800, -3500), "rent": (-1400, -1400), "supplies": (-400, -200)}.items():
            rows.append([rand_day(ms), round(random.uniform(lo, hi), 2), "vendor", cat])
    write_csv("06_thin_customer_base.csv", rows)


if __name__ == "__main__":
    print(f"Generating scenario CSVs into ./{OUT_DIR}/ ...")
    scenario_healthy()
    scenario_concentration_risk()
    scenario_negative_cash_flow()
    scenario_sharp_drop()
    scenario_high_volatility()
    scenario_thin_customer_base()
    print("Done.")