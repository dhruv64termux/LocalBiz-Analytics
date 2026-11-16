"""Reading, column auto-detection and cleaning of sales files (CSV or Excel).

Real shop data never uses the same column names, so the flow is:
  read_raw()  ->  suggest_mapping()  ->  (user can fix the mapping)  ->  clean()
"""
import re
from io import BytesIO

import numpy as np
import pandas as pd

# canonical field -> possible header names (lower-case, letters/digits only), best match first
ALIASES = {
    "order_date": ["orderdate", "invoicedate", "transactiondate", "purchasedate", "saledate", "billdate",
                   "datetime", "createdat", "timestamp", "date"],
    "product_name": ["productname", "itemname", "product", "item", "itemdescription", "productdescription",
                     "description", "particulars", "goods"],
    "unit_price": ["unitprice", "priceeach", "sellingprice", "saleprice", "priceperunit", "price", "mrp", "rate"],
    "total_sales": ["totalsales", "salesamount", "sales", "netsales", "revenue", "totalamount", "lineamount",
                    "linetotal", "amount", "total"],
    "quantity": ["quantity", "quantityordered", "qty", "unitssold", "units", "pcs", "nos"],
    "unit_cost": ["unitcost", "costprice", "purchaseprice", "costperunit", "cost", "cogs"],
    "total_profit": ["totalprofit", "netprofit", "grossprofit", "profit", "earnings"],
    "order_id": ["orderid", "ordernumber", "orderno", "invoiceno", "invoicenumber", "invoice", "billno",
                 "receiptno", "transactionid", "bill"],
    "shipping_cost": ["shippingcost", "shippingcharge", "deliverycharge", "deliverycost", "freight", "shipping"],
    "channel": ["saleschannel", "channel", "platform", "source", "segment", "outlet", "store"],
    "category": ["productcategory", "category", "department", "producttype", "group"],
    "status": ["orderstatus", "status", "paymentstatus"],
    "customer_id": ["customerid", "customercode", "clientid", "userid", "customer", "customername", "clientname"],
    "sku": ["sku", "productid", "itemcode", "stockcode", "productcode", "barcode"],
}
ALL_FIELDS = list(ALIASES)
ESSENTIAL = ["order_date", "product_name"]  # plus: unit_price OR total_sales

# (field, label shown in the mapping screen)
FIELD_LABELS = [
    ("order_date", "Order date *"), ("product_name", "Product name *"),
    ("unit_price", "Unit price (one of price / total)"), ("total_sales", "Total sales amount (one of price / total)"),
    ("quantity", "Quantity"), ("unit_cost", "Unit cost"), ("total_profit", "Total profit"),
    ("order_id", "Order / bill ID"), ("channel", "Channel"), ("category", "Category"),
    ("status", "Status"), ("customer_id", "Customer ID"), ("sku", "SKU / product code"),
    ("shipping_cost", "Shipping cost"),
]
OPTIONAL_DEFAULTS = {"customer_id": "UNKNOWN", "sku": "N/A", "category": "Uncategorised",
                     "channel": "Unknown", "status": "Completed"}
TEXT_COLS = ["order_id", "customer_id", "product_name", "sku", "category", "channel", "status"]
NUM_COLS = ["quantity", "unit_price", "total_sales", "unit_cost", "total_profit", "shipping_cost"]
REFUND_WORDS = {"refunded", "returned", "cancelled", "canceled", "refund", "return"}


def _norm(c):
    return re.sub(r"[^a-z0-9]", "", str(c).lower())


def read_raw(source, name="file.csv"):
    """source: bytes (uploaded file) or a file path. Reads CSV or Excel."""
    is_excel = str(name).lower().endswith((".xlsx", ".xls"))
    handle = BytesIO(source) if isinstance(source, (bytes, bytearray)) else name
    if is_excel:
        return pd.read_excel(handle)
    for enc in ("utf-8-sig", "latin-1"):
        try:
            if hasattr(handle, "seek"):
                handle.seek(0)
            return pd.read_csv(handle, encoding=enc)
        except UnicodeDecodeError:
            continue
    raise ValueError("Could not read the file")


def suggest_mapping(columns):
    """Guess which file column matches each field. Returns {field: column or None}."""
    by_norm = {}
    for c in columns:
        by_norm.setdefault(_norm(c), c)
    used, mapping = set(), {}
    for field in ALL_FIELDS:
        mapping[field] = None
        for alias in ALIASES[field]:
            col = by_norm.get(alias)
            if col is not None and col not in used:
                mapping[field], _ = col, used.add(col)
                break
    return mapping


def check_mapping(mapping):
    """Return a list of what is still missing (empty list = good to go)."""
    problems = []
    if not mapping.get("order_date"):
        problems.append("Order date")
    if not mapping.get("product_name"):
        problems.append("Product name")
    if not (mapping.get("unit_price") or mapping.get("total_sales")):
        problems.append("Unit price or Total sales amount")
    return problems


def _num(s):
    s = s.astype(str).str.replace(r"[₹$€£,\s]", "", regex=True)
    return pd.to_numeric(s, errors="coerce")


def _guess_dayfirst(s):
    """dd/mm vs mm/dd: look for a value that can only be one of them. Ambiguous -> day first (India)."""
    parts = s.dropna().astype(str).str.extract(r"^\s*(\d{1,2})[/\-.](\d{1,2})[/\-.]\d{2,4}")
    if parts.isna().all().all():
        return False  # ISO (2026-10-05) or text dates: no ambiguity
    first, second = pd.to_numeric(parts[0], errors="coerce"), pd.to_numeric(parts[1], errors="coerce")
    if (second > 12).any() and not (first > 12).any():
        return False
    return True


def _dates(s, dayfirst):
    if dayfirst is None:
        dayfirst = _guess_dayfirst(s)
    try:
        return pd.to_datetime(s, errors="coerce", dayfirst=dayfirst, format="mixed")
    except (TypeError, ValueError):
        return pd.to_datetime(s, errors="coerce", dayfirst=dayfirst)


def clean(raw, mapping=None, dayfirst=None):
    """Turn any sales table into the standard shape. Returns (clean_df, report)."""
    raw = raw.copy()
    raw.columns = [str(c).strip() for c in raw.columns]
    mapping = mapping or suggest_mapping(list(raw.columns))
    problems = check_mapping(mapping)
    if problems:
        raise ValueError("Please choose a column for: " + ", ".join(problems))

    df = pd.DataFrame(index=raw.index)
    for field in ALL_FIELDS:
        src = mapping.get(field)
        df[field] = raw[src] if src and src in raw.columns else np.nan

    notes = []
    report = {"rows_raw": len(df), "notes": notes, "no_cost": False}

    for c in TEXT_COLS:
        df[c] = df[c].astype(str).str.strip().replace({"nan": np.nan, "": np.nan, "None": np.nan})
    df["order_date"] = _dates(df["order_date"], dayfirst)
    for c in NUM_COLS:
        df[c] = _num(df[c])

    # ---- fill in what the file doesn't have ----
    if not mapping.get("quantity"):
        df["quantity"] = 1.0
        notes.append("No quantity column found: each row is treated as 1 unit.")
    if not mapping.get("order_id"):
        df["order_id"] = ["ROW-" + str(i + 1) for i in range(len(df))]
        notes.append("No order ID column found: each row is treated as its own order.")
    if not mapping.get("unit_price"):
        df["unit_price"] = df["total_sales"] / df["quantity"]
        notes.append("Unit price was calculated as total sales / quantity.")
    if not mapping.get("unit_cost"):
        if mapping.get("total_profit"):
            df["unit_cost"] = (df["unit_price"] * df["quantity"] - df["total_profit"]) / df["quantity"]
            notes.append("Unit cost was calculated from your profit column.")
        else:
            report["no_cost"] = True
            notes.append("No cost or profit column found: profit will equal revenue, so margins are overstated.")
    if not mapping.get("shipping_cost"):
        df["shipping_cost"] = 0.0

    # ---- duplicates: same order, time and product ----
    n = len(df)
    df = df.drop_duplicates(subset=["order_id", "order_date", "product_name"], keep="first")
    report["duplicates_removed"] = n - len(df)

    # ---- unusable rows ----
    n = len(df)
    bad = (df[["order_date", "product_name", "quantity", "unit_price"]].isna().any(axis=1)
           | (df["quantity"] <= 0) | (df["unit_price"] <= 0))
    df = df[~bad]
    report["invalid_rows_removed"] = n - len(df)

    # ---- fill gaps ----
    for col, default in OPTIONAL_DEFAULTS.items():
        report[f"filled_{col}"] = int(df[col].isna().sum())
        df[col] = df[col].fillna(default)
    if report["no_cost"]:
        report["filled_unit_cost"] = 0
        df["unit_cost"] = 0.0
    else:
        med = df.groupby("product_name")["unit_cost"].transform("median")
        report["filled_unit_cost"] = int(df["unit_cost"].isna().sum())
        df["unit_cost"] = df["unit_cost"].fillna(med).fillna(0)
    df["shipping_cost"] = df["shipping_cost"].fillna(0)

    # ---- derived money columns (refunded orders earn nothing) ----
    df["is_refunded"] = df["status"].str.lower().isin(REFUND_WORDS)
    keep = ~df["is_refunded"]
    df["units_sold"] = df["quantity"].where(keep, 0)
    df["revenue"] = (df["quantity"] * df["unit_price"]).where(keep, 0)
    df["cost"] = (df["quantity"] * df["unit_cost"] + df["shipping_cost"]).where(keep, 0)
    df["profit"] = df["revenue"] - df["cost"]
    df["date"] = df["order_date"].dt.normalize()
    df = df.drop(columns=["total_sales", "total_profit"])

    df = df.sort_values("order_date").reset_index(drop=True)
    report["rows_clean"] = len(df)
    return df, report


def load_and_clean(source, name="file.csv"):
    return clean(read_raw(source, name))
