import csv
import os
import random
from datetime import date, timedelta

random.seed(42)

OUT = os.path.dirname(os.path.abspath(__file__))

def write_csv(filename, rows):
    path = os.path.join(OUT, filename)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "amount", "counterparty", "category"])
        w.writerows(rows)
    print(f"  {filename}  ({len(rows)} rows)")

def generate_month(rows, year, month, total_revenue, customers, dominant_cust=None):
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)
    days_in_month = (end - start).days
    # 3-8 revenue transactions
    num_revenue = random.randint(3, 6)
    rev_per_tx = total_revenue / num_revenue
    for i in range(num_revenue):
        d = start + timedelta(days=random.randint(0, days_in_month - 1))
        cust = dominant_cust if dominant_cust and random.random() < 0.6 else random.choice(customers)
        rows.append([d.isoformat(), round(rev_per_tx * random.uniform(0.8, 1.2), 2), cust, "revenue"])
    # fixed costs
    rows.append([start.isoformat(), round(-random.uniform(2000, 4000), 2), "vendor", "payroll"])
    rows.append([(start + timedelta(days=5)).isoformat(), round(-random.uniform(800, 1500), 2), "vendor", "rent"])
    rows.append([(start + timedelta(days=12)).isoformat(), round(-random.uniform(100, 500), 2), "vendor", "software"])
    rows.append([(start + timedelta(days=20)).isoformat(), round(-random.uniform(200, 600), 2), "vendor", "supplies"])

# ─── 1. healthy business ─────────────────────────────────────────────
def gen_healthy():
    rows = []
    customers = ["Acme Retail Co", "Northwind Traders", "BlueSky Logistics", "Gilded Goods LLC", "Cedar & Co"]
    for m in range(1, 13):
        generate_month(rows, 2025, m, random.randint(7500, 9000), customers)
    write_csv("01_healthy_business.csv", rows)

# ─── 2. customer concentration ───────────────────────────────────────
def gen_concentration():
    rows = []
    customers = ["Acme Retail Co", "Northwind Traders", "BlueSky Logistics"]
    for m in range(1, 13):
        generate_month(rows, 2025, m, random.randint(6000, 8500), customers, dominant_cust="Acme Retail Co")
    write_csv("02_customer_concentration.csv", rows)

# ─── 3. seasonal dip ─────────────────────────────────────────────────
def gen_seasonal():
    rows = []
    customers = ["Acme Retail Co", "Northwind Traders", "Cedar & Co"]
    for m in range(1, 13):
        rev = 3000 if m in (5, 6, 7) else 8000
        generate_month(rows, 2025, m, rev, customers)
    write_csv("03_seasonal_dip.csv", rows)

# ─── 4. negative streak ──────────────────────────────────────────────
def gen_negative_streak():
    rows = []
    customers = ["Northwind Traders", "Cedar & Co"]
    for m in range(1, 13):
        rev = random.randint(2000, 3500)
        generate_month(rows, 2025, m, rev, customers)
        # extra expenses to drive net negative
        rows.append([date(2025, m, 15).isoformat(), round(-random.randint(1000, 2500), 2), "vendor", "misc"])
    write_csv("04_negative_streak.csv", rows)

# ─── 5. revenue volatility ───────────────────────────────────────────
def gen_volatility():
    rows = []
    customers = ["Acme Retail Co", "BlueSky Logistics", "Cedar & Co"]
    revenues = [12000, 3000, 11000, 2000, 14000, 2500, 13000, 2800, 10000, 4000, 15000, 3500]
    for m in range(1, 13):
        generate_month(rows, 2025, m, revenues[m - 1], customers)
    write_csv("05_revenue_volatility.csv", rows)

# ─── 6. high growth ──────────────────────────────────────────────────
def gen_growth():
    rows = []
    customers = ["Acme Retail Co", "Northwind Traders", "Cedar & Co"]
    for m in range(1, 13):
        rev = 3000 + m * 600
        generate_month(rows, 2025, m, rev, customers)
    write_csv("06_high_growth.csv", rows)

# ─── 7. missing columns ──────────────────────────────────────────────
def gen_missing_columns():
    path = os.path.join(OUT, "07_missing_columns.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "amount"])
        w.writerow(["2025-01-01", "1000"])
    print(f"  07_missing_columns.csv  (1 row, missing counterparty)")

# ─── 8. empty ────────────────────────────────────────────────────────
def gen_empty():
    path = os.path.join(OUT, "08_empty.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "amount", "counterparty", "category"])
    print(f"  08_empty.csv  (header only)")

# ─── 9. single month ─────────────────────────────────────────────────
def gen_single_month():
    rows = []
    generate_month(rows, 2025, 6, 5000, ["Acme Retail Co"])
    write_csv("09_single_month.csv", rows)

# ─── 10. non-numeric amounts ─────────────────────────────────────────
def gen_bad_amounts():
    path = os.path.join(OUT, "10_bad_amounts.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "amount", "counterparty", "category"])
        w.writerow(["2025-01-01", "abc", "Acme", "revenue"])
        w.writerow(["2025-01-02", "N/A", "Vendor", "payroll"])
        w.writerow(["2025-01-03", "12.5xyz", "Acme", "revenue"])
    print(f"  10_bad_amounts.csv  (3 rows, non-numeric amounts)")

print("Generating test data...\n")
gen_healthy()
gen_concentration()
gen_seasonal()
gen_negative_streak()
gen_volatility()
gen_growth()
gen_missing_columns()
gen_empty()
gen_single_month()
gen_bad_amounts()
print("\nDone — 10 files in test-data/")
