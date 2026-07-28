import random
from datetime import date
from _helpers import month_start, write_csv, generate_month

random.seed(42)

CUSTOMERS = ["Acme Retail Co", "Northwind Traders", "BlueSky Logistics", "Gilded Goods LLC", "Cedar & Co"]
BASE = date(2025, 1, 1)
rows = []

for month_offset in range(12):
    is_slow_month = month_offset in (5, 6)
    total_revenue = 8000 if not is_slow_month else 3500
    generate_month(rows, BASE, month_offset, total_revenue, CUSTOMERS, dominant_cust=CUSTOMERS[0])

write_csv("sme_transactions_sample.csv", rows)
