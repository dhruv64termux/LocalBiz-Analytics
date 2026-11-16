"""Generate a realistic but FICTIONAL sales dataset for 'Coastal Retail - Mangaluru'.

Run:  python generate_data.py
Output: data/sales_data.csv  (deliberately a little messy so the cleaning module has work to do)
"""
from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(42)

# name, sku, category, price, cost, popularity weight, return probability
PRODUCTS = [
    ("Mangalore Special Roasted Cashews (W240, 500g)", "SKU-1042", "Snacks", 400, 264, 1.7, 0.02),
    ("Cold-Pressed Virgin Coconut Oil (1L)", "SKU-2088", "Groceries", 350, 252, 1.3, 0.02),
    ("Coastal Masala Spices & Byadgi Chilli Mix (250g)", "SKU-3112", "Groceries", 300, 168, 1.2, 0.01),
    ("Artisanal Jackfruit Chips & Banana Crisps Combo", "SKU-1854", "Snacks", 250, 160, 1.0, 0.02),
    ("Imported Almond Milk 1L", "SKU-4902", "Beverages", 370, 354, 0.6, 0.03),
    ("Ceramic Coffee Mug & Filter Set", "SKU-5810", "Home & Kitchen", 1200, 1120, 0.35, 0.09),
    ("Organic Bamboo Toothbrush Pack", "SKU-1190", "Personal Care", 280, 260, 0.5, 0.02),
    ("Flaxseed Dietary Crackers 200g", "SKU-7721", "Snacks", 150, 137, 0.2, 0.02),
]

N_ORDERS = 3200
days = pd.date_range("2026-03-01", "2026-10-31", freq="D")
month_idx = np.asarray((days.year - 2026) * 12 + days.month - 3)
day_w = (1 + 0.07 * month_idx) * np.where(np.asarray(days.day_of_week) >= 5, 1.5, 1.0)
day_w = day_w / day_w.sum()

order_days = rng.choice(days, size=N_ORDERS, p=day_w)
secs = rng.integers(10 * 3600, 21 * 3600, size=N_ORDERS)
order_dt = pd.to_datetime(order_days) + pd.to_timedelta(secs, unit="s")
order_dt = np.sort(order_dt.values)

p_w = np.array([p[5] for p in PRODUCTS])
p_idx = rng.choice(len(PRODUCTS), size=N_ORDERS, p=p_w / p_w.sum())

rows = []
last_day = pd.Timestamp("2026-10-30")
for i in range(N_ORDERS):
    name, sku, cat, price, cost, _, ret_p = PRODUCTS[p_idx[i]]
    channel = "Online Store" if rng.random() < 0.386 else "In-Store POS"
    ship = 0 if channel == "In-Store POS" else int(rng.integers(40, 90))
    if sku == "SKU-4902" and channel == "Online Store":
        ship *= 2  # heavy imported item -> expensive shipping
    ts = pd.Timestamp(order_dt[i])
    if rng.random() < ret_p:
        status = "Refunded"
    elif ts >= last_day and rng.random() < 0.4:
        status = "Processing"
    else:
        status = "Completed"
    rows.append(
        dict(
            order_id=f"ORD-{1001 + i}",
            order_date=ts.strftime("%Y-%m-%d %H:%M:%S"),
            customer_id=f"CUST-{int(rng.integers(1, 2600)):04d}",
            product_name=name,
            sku=sku,
            category=cat,
            channel=channel,
            quantity=int(rng.choice([1, 2, 3, 4], p=[0.55, 0.28, 0.12, 0.05])),
            unit_price=price,
            unit_cost=cost,
            shipping_cost=ship,
            status=status,
        )
    )

df = pd.DataFrame(rows)

# ---- make it realistically messy ----
dups = df.sample(25, random_state=1)
df = pd.concat([df, dups], ignore_index=True)
df.loc[df.sample(15, random_state=2).index, "quantity"] = np.nan
df.loc[df.sample(10, random_state=3).index, "channel"] = np.nan
df.loc[df.sample(20, random_state=4).index, "product_name"] += "  "
df.loc[df.sample(8, random_state=5).index, "unit_cost"] = np.nan
df = df.sample(frac=1, random_state=7).reset_index(drop=True)

out = Path(__file__).parent / "data" / "sales_data.csv"
out.parent.mkdir(exist_ok=True)
df.to_csv(out, index=False)
print(f"Saved {len(df):,} rows -> {out}")
