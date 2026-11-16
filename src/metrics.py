"""All business calculations. No Streamlit code in here, so it is easy to test."""
import pandas as pd


def split_periods(df, start, end):
    """Current period and the equally long period right before it."""
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    span = (end - start) + pd.Timedelta(days=1)
    cur = df[(df["date"] >= start) & (df["date"] <= end)]
    prev = df[(df["date"] >= start - span) & (df["date"] < start)]
    return cur, prev


def summary(df):
    revenue, profit = df["revenue"].sum(), df["profit"].sum()
    orders = int(df.loc[~df["is_refunded"], "order_id"].nunique())
    return {
        "revenue": revenue,
        "profit": profit,
        "orders": orders,
        "aov": revenue / orders if orders else 0,
        "margin": profit / revenue * 100 if revenue else 0,
        "items_per_order": df["units_sold"].sum() / orders if orders else 0,
        "refunded": int(df["is_refunded"].sum()),
        "pending": int(df["status"].str.lower().eq("processing").sum()),
    }


def pct_change(cur, prev):
    return None if not prev else (cur - prev) / abs(prev) * 100


def trend(df, freq="MS"):
    if df.empty:
        return pd.DataFrame(columns=["order_date", "revenue", "profit"])
    return (
        df.set_index("order_date")[["revenue", "profit"]]
        .resample(freq).sum().reset_index()
    )


def channel_monthly(df):
    d = df.assign(month=df["order_date"].dt.to_period("M").dt.to_timestamp())
    return d.groupby(["month", "channel"])["revenue"].sum().reset_index()


def channel_split(df):
    g = df[~df["is_refunded"]].groupby("channel").agg(
        revenue=("revenue", "sum"), orders=("order_id", "nunique")
    )
    g["share"] = g["revenue"] / g["revenue"].sum() * 100 if len(g) else 0
    return g.sort_values("revenue", ascending=False).reset_index()


def product_table(df):
    g = df.groupby(["product_name", "sku"]).agg(
        revenue=("revenue", "sum"),
        profit=("profit", "sum"),
        units=("units_sold", "sum"),
        orders=("order_id", "count"),
        refunds=("is_refunded", "sum"),
    ).reset_index()
    g["margin_pct"] = (g["profit"] / g["revenue"] * 100).fillna(0)
    g["return_rate"] = g["refunds"] / g["orders"] * 100
    return g.sort_values("revenue", ascending=False).reset_index(drop=True)


def periodic_series(df, freq="W"):
    """Revenue / profit / orders / AOV per period (used for KPI sparklines)."""
    if df.empty:
        return pd.DataFrame(columns=["order_date", "revenue", "profit", "orders", "aov"])
    d = df.assign(ok=df["order_id"].where(~df["is_refunded"])).set_index("order_date")
    g = d.resample(freq).agg({"revenue": "sum", "profit": "sum", "ok": "nunique"}).rename(columns={"ok": "orders"})
    safe = g["orders"].where(g["orders"] > 0, 1)
    g["aov"] = (g["revenue"] / safe).where(g["orders"] > 0, 0.0)
    return g.reset_index()


def attention_products(pt, margin_floor=10, return_ceiling=7, slow_ratio=0.3):
    """Products that need action, with coloured tags and a suggested action."""
    cols = list(pt.columns) + ["tags", "issue", "action"]
    med_units = pt["units"].median() if len(pt) else 0
    rows = []
    for r in pt.to_dict("records"):
        tags = []
        slow = bool(med_units) and r["units"] < slow_ratio * med_units
        if r["profit"] < 0:
            tags.append(("Losing money", "red"))
        if r["margin_pct"] < margin_floor:
            tags.append(("Low margin", "red"))
        if r["return_rate"] >= return_ceiling:
            tags.append((f"Return rate {r['return_rate']:.1f}%", "orange"))
        if slow:
            tags.append(("Slow moving", "blue"))
        if not tags:
            continue
        if r["profit"] < 0:
            action = "Adjust Price"
        elif r["return_rate"] >= return_ceiling:
            action = "Bundle"
        elif slow:
            action = "Discount 15%"
        else:
            action = "Renegotiate"
        rows.append({**r, "tags": tags, "issue": " / ".join(t for t, _ in tags), "action": action})
    if not rows:
        return pd.DataFrame(columns=cols)
    return pd.DataFrame(rows).sort_values("margin_pct").reset_index(drop=True)


def insights(df, history=None):
    """Auto-generated business insights.
    Peak day comes from the selected period; repeat customers and sales velocity
    use the full history up to the end date so they have enough data to compare."""
    history = df if history is None else history
    ok = df[~df["is_refunded"]]
    hok = history[~history["is_refunded"]]
    out = {}

    by_day = ok.groupby(ok["order_date"].dt.day_name())["revenue"].sum()
    if len(by_day):
        day = by_day.idxmax()
        sub = ok[ok["order_date"].dt.day_name() == day]
        by_hour = sub.groupby(sub["order_date"].dt.hour)["revenue"].sum().reindex(range(24), fill_value=0)
        win = by_hour.rolling(3).sum()
        end_h = int(win.idxmax())
        out["peak_day"] = (day, by_day.max() / by_day.sum() * 100, end_h - 2, end_h + 1,
                           win.max() / by_hour.sum() * 100)

    per_cust = hok.groupby("customer_id").agg(orders=("order_id", "nunique"), rev=("revenue", "sum"))
    per_cust = per_cust[per_cust.index != "UNKNOWN"]
    rep = per_cust[per_cust["orders"] > 1]
    if len(per_cust) and per_cust["rev"].sum():
        out["repeat"] = (len(rep), rep["rev"].sum(), rep["rev"].sum() / per_cust["rev"].sum() * 100)

    if len(hok):
        last = hok["date"].max()
        recent = hok[hok["date"] > last - pd.Timedelta(days=30)].groupby("product_name")["units_sold"].sum()
        before = hok[(hok["date"] <= last - pd.Timedelta(days=30)) & (hok["date"] > last - pd.Timedelta(days=60))] \
            .groupby("product_name")["units_sold"].sum()
        growth = (recent / before.where(before > 0)).dropna()
        growth = growth[before.reindex(growth.index) >= 10]  # ignore tiny baselines
        growth = growth[recent.reindex(growth.index) >= recent.median()]  # only products with real volume
        if len(growth):
            out["velocity"] = (growth.idxmax(), float(growth.max()), int(recent[growth.idxmax()]))
    return out
