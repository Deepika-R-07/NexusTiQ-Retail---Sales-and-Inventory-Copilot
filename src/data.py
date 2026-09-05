import csv
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_data(products_file, stores_file, sales_file):
    products = read_csv(products_file)
    stores = read_csv(stores_file)
    sales = read_csv(sales_file)
    for p in products:
        p["unit_price"] = float(p["unit_price"])
        p["reorder_point"] = int(p["reorder_point"])
        p["lead_time_days"] = int(p["lead_time_days"])
        p["stock"] = int(p["stock"])
    for s in sales:
        s["quantity"] = int(s["quantity"])
        s["unit_price"] = float(s["unit_price"])
    return products, stores, sales


def product_map(products):
    return {p["product_id"]: p for p in products}


def store_map(stores):
    return {s["store_id"]: s for s in stores}


def sales_by_product(sales):
    out = defaultdict(int)
    for row in sales:
        out[row["product_id"]] += row["quantity"]
    return out


def sales_by_product_store(sales):
    out = defaultdict(int)
    for row in sales:
        out[(row["product_id"], row["store_id"])] += row["quantity"]
    return out


def revenue(row):
    return row["quantity"] * row["unit_price"]


def month_label(d):
    return d.strftime("%Y-%m")


def current_month(sales):
    months = sorted({r["date"][:7] for r in sales})
    return months[-1] if months else None


def previous_month(sales):
    months = sorted({r["date"][:7] for r in sales})
    return months[-2] if len(months) > 1 else None
