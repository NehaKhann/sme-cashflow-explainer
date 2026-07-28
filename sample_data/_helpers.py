import csv
import random
from datetime import date, timedelta


def month_start(base: date, offset: int) -> date:
    y = base.year + (base.month - 1 + offset) // 12
    m = (base.month - 1 + offset) % 12 + 1
    return date(y, m, 1)


def rand_day(month_start_date: date) -> date:
    return month_start_date + timedelta(days=random.randint(1, 27))


def write_csv(filename: str, rows: list) -> None:
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "amount", "counterparty", "category"])
        for r in sorted(rows, key=lambda x: x[0]):
            writer.writerow(r)
    print(f"  wrote {filename}  ({len(rows)} rows)")


def add_revenue(rows: list, month_start_date: date, total: float, customers: list[str]) -> None:
    share = total / len(customers)
    for cust in customers:
        amt = round(share * random.uniform(0.85, 1.15), 2)
        rows.append([rand_day(month_start_date), amt, cust, "revenue"])


def add_dominant_revenue(rows: list, month_start_date: date, total: float,
                          dominant_cust: str, other_customers: list[str],
                          dominant_share: float = 0.55) -> None:
    dominant_amt = round(total * random.uniform(dominant_share - 0.05, dominant_share + 0.05), 2)
    rows.append([rand_day(month_start_date), dominant_amt, dominant_cust, "revenue"])
    remaining = total - dominant_amt
    for cust in other_customers:
        amt = round(remaining / len(other_customers) * random.uniform(0.7, 1.3), 2)
        rows.append([rand_day(month_start_date), amt, cust, "revenue"])


DEFAULT_EXPENSES: dict = {
    "payroll": (-4500, -3800),
    "rent": (-1500, -1500),
    "supplies": (-900, -300),
    "software": (-250, -150),
    "utilities": (-350, -200),
}


def add_expenses(rows: list, month_start_date: date, expenses: dict = None) -> None:
    for cat, (lo, hi) in (expenses or DEFAULT_EXPENSES).items():
        amt = round(random.uniform(lo, hi), 2)
        rows.append([rand_day(month_start_date), amt, "vendor", cat])


def generate_month(rows: list, base: date, month_offset: int,
                   total_revenue: float, customers: list[str],
                   dominant_cust: str = None, expenses: dict = None) -> None:
    ms = month_start(base, month_offset)
    if dominant_cust:
        add_dominant_revenue(rows, ms, total_revenue, dominant_cust,
                             [c for c in customers if c != dominant_cust])
    else:
        add_revenue(rows, ms, total_revenue, customers)
    add_expenses(rows, ms, expenses)
