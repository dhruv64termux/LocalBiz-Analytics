"""LocalBiz Analytics - Sales Intelligence Dashboard (Streamlit), styled after the Stitch design."""
import html
import re
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import metrics as m
from src.cleaning import FIELD_LABELS, check_mapping, clean, read_raw, suggest_mapping

DATA_PATH = Path(__file__).parent / "data" / "sales_data.csv"
INDIGO, CYAN, GREEN, RED, PINK, AMBER = "#8b8ff5", "#6ec6ff", "#4ade80", "#f87171", "#fca5a5", "#fbbf24"

st.set_page_config(page_title="LocalBiz Analytics", page_icon="📊", layout="wide")

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, .stApp, .stApp p, .stApp label, .stApp button, .stApp input, .stApp textarea {font-family:'Inter',sans-serif;}
[data-testid="stIconMaterial"], span[class*="material"] {font-family:"Material Symbols Rounded" !important;}
.stApp {background:#0a0f1d;}
.block-container {padding:1.2rem 2rem 3rem; max-width:1500px;}
header[data-testid="stHeader"] {background:transparent;}
.stAppDeployButton, #MainMenu {display:none;}

/* sidebar */
[data-testid="stSidebar"] {background:#070b16; border-right:1px solid #161e36;}
[data-testid="stSidebar"] .stButton button {justify-content:flex-start; border-radius:10px; padding:9px 12px;}
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {background:transparent; border:none; color:#cfd4ee;}
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover {background:#111a2e; color:#fff;}
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {border:none; font-weight:600;}
.logo {display:flex; align-items:center; gap:10px; font-weight:700; font-size:18px; margin-bottom:14px;}
.logo .mark {background:#1b2650; width:34px; height:34px; border-radius:9px; display:flex; align-items:center; justify-content:center;}
.logo .pro {margin-left:auto; font-size:10px; background:#232b5e; color:#a5a8ff; padding:3px 8px; border-radius:8px;}
.sync {background:#0f1628; border:1px solid #1c2641; border-radius:10px; padding:9px 12px; font-size:12px; margin-bottom:14px; color:#cfd4ee;}
.sync .dot {display:inline-block; width:8px; height:8px; border-radius:50%; background:#4ade80; margin-right:8px;}
.profile {display:flex; align-items:center; gap:10px; background:#0f1628; border:1px solid #1c2641; border-radius:12px; padding:10px 12px; margin-top:40px;}
.avatar {width:34px; height:34px; border-radius:50%; background:#2b3470; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:13px;}

[data-testid="stSidebar"] .stButton button > div {justify-content:flex-start; width:100%;}
[data-testid="stSidebar"] .stButton button p {text-align:left;}
.bizpill {background:#111a2e; border:1px solid #1c2641; border-radius:10px; padding:9px 14px; font-size:14px; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;}

/* generic cards */
[class*="st-key-card"] {background:#111a2e; border:1px solid #1c2641; border-radius:16px; padding:20px 22px;}
.card {background:#111a2e; border:1px solid #1c2641; border-radius:16px; padding:20px 22px; min-height:400px;}
.title {font-size:18px; font-weight:600; margin-bottom:2px;}
.muted {color:#8b93b5; font-size:12px;}

/* KPI */
.kcard {background:#111a2e; border:1px solid #1c2641; border-radius:16px; padding:16px 18px; height:200px; display:flex; flex-direction:column;}
.khead {display:flex; align-items:center; gap:10px;}
.kicon {width:32px; height:32px; border-radius:9px; display:flex; align-items:center; justify-content:center; font-size:15px;}
.klabel {font-size:11px; letter-spacing:.07em; color:#9aa3c7; text-transform:uppercase; font-weight:600; line-height:1.2;}
.chip {margin-left:auto; font-size:11px; font-weight:600; padding:3px 9px; border-radius:8px; white-space:nowrap;}
.chip.up {background:#10301f; color:#4ade80;}
.chip.down {background:#3a1a1f; color:#f87171;}
.kvalue {font-size:34px; font-weight:700; margin:10px 0 2px 0; color:#fff; letter-spacing:-.5px;}
.kviz {height:40px; margin-top:auto;}
.kfoot {display:flex; justify-content:space-between; font-size:11.5px; color:#9aa3c7; margin-top:8px;}
.kfoot b {color:#e6e9f5;}
.green {color:#4ade80; font-weight:600;}

/* product rows */
.prow {padding:11px 0;}
.prow .top {display:flex; justify-content:space-between; align-items:center;}
.num {display:inline-flex; width:22px; height:22px; border-radius:50%; background:#12301f; color:#4ade80; align-items:center; justify-content:center; font-size:11px; font-weight:700; margin-right:10px;}
.bar-bg {background:#1c2641; border-radius:6px; height:5px; margin-top:7px;}
.bar-fg {height:5px; border-radius:6px; background:linear-gradient(90deg,#a5a8ff,#4ade80);}
.tag {font-size:10px; font-weight:600; padding:2px 8px; border-radius:6px; margin-left:8px; white-space:nowrap;}
.tag.red {background:#3a1a1f; color:#f87171;}
.tag.orange {background:#3a2a17; color:#fbbf24;}
.tag.blue {background:#14304a; color:#6ec6ff;}
.badge {font-size:11px; font-weight:600; padding:3px 10px; border-radius:8px; background:#3a1a1f; color:#f87171; margin-left:10px;}
.arow {display:flex; justify-content:space-between; align-items:center; padding:14px 14px; margin-top:10px; background:#0d1424; border-radius:12px;}
.abtn {font-size:12px; font-weight:600; padding:7px 14px; border-radius:8px; background:#1c2641; color:#e6e9f5; white-space:nowrap;}

/* insights */
.icard {background:#111a2e; border:1px solid #1c2641; border-radius:16px; padding:20px 22px; min-height:250px;}
.ihead {display:flex; align-items:center; gap:10px; margin-bottom:12px;}
.iicon {width:38px; height:38px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:17px;}
.ilabel {font-size:11px; letter-spacing:.08em; font-weight:700; text-transform:uppercase;}
.ititle {font-size:17px; font-weight:600; margin-bottom:8px;}
.itext {font-size:13px; color:#aab1d3; line-height:1.55; margin-bottom:16px;}
.ibtn {text-align:center; font-size:13px; font-weight:600; padding:10px; border-radius:10px; background:#161f38; color:#c9cdf5;}
.ibtn.primary {background:#8b8ff5; color:#0a0f1d;}

/* channel mini cards */
.mini {background:#0d1424; border-radius:12px; padding:12px 14px;}
.mini .dot {display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:6px;}
.mini .amt {font-size:20px; font-weight:700; margin:4px 0 2px;}

/* transactions table */
table.tx {width:100%; border-collapse:collapse; margin-top:10px;}
table.tx th {font-size:10.5px; letter-spacing:.07em; color:#8b93b5; text-align:left; padding:10px 8px; border-bottom:1px solid #1c2641; text-transform:uppercase;}
table.tx td {padding:14px 8px; border-bottom:1px solid #161e36; font-size:13px; vertical-align:middle;}
.pill {font-size:11px; font-weight:600; padding:4px 10px; border-radius:20px;}
.pill.completed {background:#10301f; color:#4ade80;}
.pill.processing {background:#14304a; color:#6ec6ff;}
.pill.refunded {background:#3a1a1f; color:#f87171;}
.chan {background:#0d1424; padding:5px 10px; border-radius:8px; font-size:12px; white-space:nowrap;}

/* header controls */
.st-key-importbtn button, .st-key-importbtn [data-testid="stPopoverButton"] {background:#232b5e; border:1px solid #3a4590; color:#c9cdf5;}
</style>
""",
    unsafe_allow_html=True,
)


# ---------------- helpers ----------------
def inr(x):
    x = round(float(x))
    s = str(abs(x))
    if len(s) > 3:
        s = re.sub(r"(\d)(?=(\d\d)+$)", r"\1,", s[:-3]) + "," + s[-3:]
    return ("-" if x < 0 else "") + "₹" + s


def spark(vals, color):
    vals = [float(v) for v in vals]
    if len(vals) < 2:
        return ""
    w, h = 200, 40
    lo, hi = min(vals), max(vals)
    rg = (hi - lo) or 1
    pts = [(i / (len(vals) - 1) * w, h - 4 - (v - lo) / rg * (h - 10)) for i, v in enumerate(vals)]
    line = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    gid = "g" + color.strip("#")
    return (
        f'<svg viewBox="0 0 {w} {h}" preserveAspectRatio="none" style="width:100%;height:40px">'
        f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{color}" stop-opacity=".35"/>'
        f'<stop offset="1" stop-color="{color}" stop-opacity="0"/></linearGradient></defs>'
        f'<path d="{line} L{w},{h} L0,{h} Z" fill="url(#{gid})"/>'
        f'<path d="{line}" fill="none" stroke="{color}" stroke-width="2" vector-effect="non-scaling-stroke"/></svg>'
    )


def bars(vals):
    vals = [float(v) for v in vals][-10:]
    mx = max(vals) or 1
    out = ""
    for i, v in enumerate(vals):
        c = CYAN if i >= len(vals) - 2 else "#2a3354"
        out += f'<div style="flex:1;height:{max(6, v / mx * 38):.0f}px;background:{c};border-radius:3px"></div>'
    return f'<div style="display:flex;gap:4px;align-items:flex-end;height:40px">{out}</div>'


def kpi(icon, icon_bg, label, value, delta, viz, left, right, invert=False):
    chip = ""
    if delta is not None:
        good = (delta >= 0) != invert
        chip = f'<span class="chip {"up" if good else "down"}">{"↗" if delta >= 0 else "↘"} {delta:+.1f}%</span>'
    return (
        f'<div class="kcard"><div class="khead"><div class="kicon" style="background:{icon_bg}">{icon}</div>'
        f'<div class="klabel">{label}</div>{chip}</div><div class="kvalue">{value}</div>'
        f'<div class="kviz">{viz}</div><div class="kfoot"><span>{left}</span><span>{right}</span></div></div>'
    )


def axis_fmt(maxv):
    vals = np.linspace(0, maxv * 1.08, 5)
    if maxv >= 1e5:
        txt = [f"₹{v / 1e5:.1f}L" for v in vals]
    else:
        txt = [f"₹{v / 1e3:.0f}K" for v in vals]
    return list(vals), txt


def hr(h):
    return f"{(h % 12) or 12} {'AM' if h < 12 else 'PM'}"


@st.cache_data(show_spinner=False)
def read_file(file_bytes, name):
    return read_raw(file_bytes, name)


@st.cache_data(show_spinner=False)
def load_clean(file_bytes, name, mapping_items, dayfirst):
    return clean(read_file(file_bytes, name), dict(mapping_items), dayfirst)


def mapping_panel(raw, auto, fname):
    """Let the user check / fix which file column means what."""
    cols = ["— none —"] + list(raw.columns)
    missing = check_mapping(auto)
    title = "🔧 Match your columns — action needed" if missing else "🔧 Columns detected automatically (click to review)"
    mapping = {}
    with st.expander(title, expanded=bool(missing)):
        st.caption("Tell the dashboard which column in your file means what. Fields marked * are required, and you need "
                   "either a unit price or a total sales amount. Everything else is optional.")
        grid = st.columns(3)
        for i, (field, label) in enumerate(FIELD_LABELS):
            guess = auto.get(field)
            sel = grid[i % 3].selectbox(label, cols, index=cols.index(guess) if guess in cols else 0, key=f"map_{fname}_{field}")
            mapping[field] = None if sel == "— none —" else sel
        fmt = st.radio("Date format", ["Auto-detect", "Day first (31/12/2026)", "Month first (12/31/2026)"],
                       horizontal=True, key=f"datefmt_{fname}")
        st.dataframe(raw.head(5), hide_index=True, width="stretch")
    return mapping, {"Auto-detect": None, "Day first (31/12/2026)": True, "Month first (12/31/2026)": False}[fmt]


def dark(fig, h=300):
    fig.update_layout(height=h, margin=dict(l=0, r=0, t=6, b=0), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#9aa3c7", size=11),
                      hoverlabel=dict(bgcolor="#1a2342", font_color="#fff"), legend=dict(orientation="h", y=1.12, x=0))
    fig.update_xaxes(gridcolor="#1c2641", zeroline=False)
    fig.update_yaxes(gridcolor="#1c2641", zeroline=False)
    return fig


PLOT_CFG = {"displayModeBar": False}
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def page_title(t, sub):
    st.markdown(f"<div style='font-size:20px;font-weight:700'>{t}</div><div class='muted'>{sub}</div>", unsafe_allow_html=True)
    st.write("")


# ---------------- sidebar ----------------
with st.sidebar:
    st.markdown('<div class="logo"><div class="mark">📊</div>LocalBiz<span class="pro">PRO</span></div>', unsafe_allow_html=True)
    pill_slot = st.empty()
    PAGES = [("Overview", "🏠"), ("Sales Analytics", "📈"), ("Product Performance", "📦"),
             ("Data Management", "🗄️"), ("Reports", "📄"), ("Settings", "⚙️")]
    if "page" not in st.session_state:
        st.session_state.page = "Overview"
    for _name, _icon in PAGES:
        st.button(f"{_icon}  {_name}", key=f"nav_{_name}", width="stretch",
                  type="primary" if st.session_state.page == _name else "secondary",
                  on_click=lambda n=_name: st.session_state.update(page=n))
    page = st.session_state.page
    profile_slot = st.empty()

# ---------------- header row ----------------
hc = st.columns([2.4, 2.0, 2.1, 1.15, 1.15, 0.9], vertical_alignment="center")
with hc[3].container(key="importbtn"):
    with st.popover("⬆ Import CSV", width="stretch"):
        upload = st.file_uploader("Upload a sales file", type=["csv", "xlsx"])
        st.caption("Any CSV or Excel file with a date, a product and a price or sales amount. "
                   "Column names are detected automatically, and you can fix them if needed.")

if upload is None and not DATA_PATH.exists():
    st.error("No data found. Run `python generate_data.py` first, or import a file.")
    st.stop()

src_bytes = upload.getvalue() if upload else None
src_name = upload.name if upload else str(DATA_PATH)
try:
    raw = read_file(src_bytes, src_name)
except Exception:
    st.error("Could not read this file. Please upload a valid CSV or Excel (.xlsx) file.")
    st.stop()

mapping, dayfirst = suggest_mapping(list(raw.columns)), None
if upload:
    mapping, dayfirst = mapping_panel(raw, mapping, upload.name)
problems = check_mapping(mapping)
if problems:
    st.error("Please choose a column for: " + ", ".join(problems))
    st.stop()
try:
    df, report = load_clean(src_bytes, src_name, tuple(sorted(mapping.items())), dayfirst)
except ValueError as e:
    st.error(str(e))
    st.stop()
if df.empty:
    st.error("No usable rows were found. Check the column mapping and the date format.")
    st.stop()

BIZ = st.session_state.get("biz_name") or ("My Business" if upload else "Demo Store")
_ini = "".join(w[0] for w in BIZ.split()[:2]).upper() or "B"
profile_slot.markdown(
    f'<div class="profile"><div class="avatar">{html.escape(_ini)}</div><div><b style="font-size:13px">{html.escape(BIZ)}</b><br>'
    f'<span class="muted">{"Your data" if upload else "Sample data"}</span></div></div>',
    unsafe_allow_html=True,
)
pill_slot.markdown(
    f'<div class="sync"><span class="dot"></span>{html.escape(upload.name) + " loaded" if upload else "Sample CSV loaded"}</div>',
    unsafe_allow_html=True,
)

if report["no_cost"]:
    st.warning("No cost or profit column was found, so profit equals revenue and margins look too high. "
               "Map a cost or profit column to see real margins.")
if report["notes"]:
    with st.expander("ℹ️ How your file was interpreted"):
        for _n in report["notes"]:
            st.write("• " + _n)

dmin, dmax = df["date"].min().date(), df["date"].max().date()
with hc[2]:
    rng = st.date_input("Date range", (dmax.replace(day=1), dmax), min_value=dmin, max_value=dmax, label_visibility="collapsed")
hc[1].markdown(f'<div class="bizpill">🏪 {html.escape(BIZ)}</div>', unsafe_allow_html=True)
if not isinstance(rng, tuple) or len(rng) != 2:
    st.info("Pick an end date to continue.")
    st.stop()
start, end = rng

filters = hc[5].popover("⚙", width="stretch")
with filters:
    st.markdown("**Filters**")
    channels = st.multiselect("Channel", sorted(df["channel"].unique()), default=sorted(df["channel"].unique()))
    cats = st.multiselect("Category", sorted(df["category"].unique()), default=sorted(df["category"].unique()))

base = df[df["channel"].isin(channels) & df["category"].isin(cats)]
cur, prev = m.split_periods(base, start, end)
if cur.empty:
    st.warning("No orders match these filters.")
    st.stop()
S, P = m.summary(cur), m.summary(prev)
THR = dict(margin_floor=st.session_state.get("margin_floor", 10), return_ceiling=st.session_state.get("return_ceiling", 7))
hist = base[base["date"] <= pd.Timestamp(end)]

with filters:
    target = st.number_input("Revenue target (₹)", min_value=0, step=10000,
                             value=int(round(P["revenue"] * 1.1, -3)) if P["revenue"] else 100000)
    with st.expander("Data quality report"):
        st.write(
            f"Rows in file: **{report['rows_raw']:,}**  \n"
            f"Duplicates removed: **{report['duplicates_removed']}**  \n"
            f"Invalid rows removed: **{report['invalid_rows_removed']}**  \n"
            f"Missing costs estimated: **{report['filled_unit_cost']}**  \n"
            f"Clean rows used: **{report['rows_clean']:,}**"
        )

hc[0].markdown(
    f"<div style='font-size:20px;font-weight:700'>Welcome back 👋</div>"
    f"<div class='muted'>Here is your sales performance overview</div>",
    unsafe_allow_html=True,
)


def build_report():
    buf = BytesIO()
    pt_ = m.product_table(cur)
    att_ = m.attention_products(pt_, **THR).drop(columns=["tags"], errors="ignore")
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        pd.DataFrame([S]).T.rename(columns={0: "value"}).to_excel(xw, sheet_name="KPIs")
        m.trend(cur, "MS").to_excel(xw, sheet_name="Monthly", index=False)
        pt_.to_excel(xw, sheet_name="Products", index=False)
        att_.to_excel(xw, sheet_name="Needs attention", index=False)
        cur.drop(columns=["date"]).to_excel(xw, sheet_name="Clean data", index=False)
    return buf.getvalue()


hc[4].download_button("⬇ Export", build_report(), "localbiz_report.xlsx", width="stretch",
                      mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
st.write("")

if page == "Overview":
    # ---------------- KPI cards ----------------
    weekly = m.periodic_series(cur, "W")
    daily = m.periodic_series(cur, "D")
    series = weekly if len(weekly) >= 4 else daily
    achieved = S["revenue"] / target * 100 if target else 0
    margin_delta = S["margin"] - P["margin"] if P["revenue"] else 0
    trend_txt = "Stable" if abs(margin_delta) < 1 else ("Improving" if margin_delta > 0 else "Declining")

    k = st.columns(4)
    k[0].markdown(kpi("💰", "#1c2a52", "Total<br>Revenue", inr(S["revenue"]), m.pct_change(S["revenue"], P["revenue"]),
                      spark(series["revenue"], INDIGO), f"Target: {inr(target)}", f'<span class="green">{achieved:.0f}% achieved</span>'), unsafe_allow_html=True)
    k[1].markdown(kpi("📈", "#12301f", "Total<br>Profit", inr(S["profit"]), m.pct_change(S["profit"], P["profit"]),
                      spark(series["profit"], GREEN), f"Net Margin: <b>{S['margin']:.1f}%</b>", f'<span style="color:{CYAN}">● {trend_txt}</span>'), unsafe_allow_html=True)
    k[2].markdown(kpi("🧾", "#14304a", "Total<br>Orders", f"{S['orders']:,}", m.pct_change(S["orders"], P["orders"]),
                      bars(daily["orders"]), f"Completed: <b>{S['orders'] - S['pending']:,}</b>", f"Pending: <b>{S['pending']}</b>"), unsafe_allow_html=True)
    k[3].markdown(kpi("🛒", "#2a2140", "Average<br>Order Value", inr(S["aov"]), m.pct_change(S["aov"], P["aov"]),
                      spark(series["aov"], PINK), f"Avg {S['items_per_order']:.1f} items/order", f"vs {inr(P['aov'])} prev" if P["aov"] else ""), unsafe_allow_html=True)
    st.write("")

    # ---------------- charts (trend uses full history up to the end date) ----------------
    hist = base[base["date"] <= pd.Timestamp(end)]
    c1, c2 = st.columns([1.55, 1])
    with c1.container(key="card_trend"):
        th, tg = st.columns([2.2, 1.4], vertical_alignment="center")
        th.markdown(
            f"<div class='title'>Revenue & Profit Growth</div><div class='muted'>Revenue velocity and profit trends "
            f"({hist['date'].min():%b} – {hist['date'].max():%b %Y})</div>", unsafe_allow_html=True)
        with tg:
            gran = st.segmented_control("Granularity", ["Daily", "Weekly", "Monthly"], default="Monthly",
                                        key="gran", label_visibility="collapsed") or "Monthly"
        t = m.trend(hist, {"Daily": "D", "Weekly": "W", "Monthly": "MS"}[gran])
        tv, tt = axis_fmt(max(t["revenue"].max(), 1))
        fig = go.Figure()
        fig.add_scatter(x=t["order_date"], y=t["revenue"], name="Gross Revenue", mode="lines", line=dict(color=INDIGO, width=2.5, shape="spline"),
                        fill="tozeroy", fillcolor="rgba(139,143,245,.15)")
        fig.add_scatter(x=t["order_date"], y=t["profit"], name="Net Profit", mode="lines", line=dict(color=CYAN, width=2.5, shape="spline"),
                        fill="tozeroy", fillcolor="rgba(110,198,255,.12)")
        fig.add_scatter(x=[t["order_date"].iloc[-1]] * 2, y=[t["revenue"].iloc[-1], t["profit"].iloc[-1]], mode="markers",
                        marker=dict(color=[INDIGO, CYAN], size=8), showlegend=False, hoverinfo="skip")
        fig.update_layout(
            height=340, margin=dict(l=0, r=0, t=6, b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#9aa3c7", size=11), hovermode="x unified",
            hoverlabel=dict(bgcolor="#1a2342", font_color="#fff", bordercolor="#2a3354"),
            legend=dict(orientation="h", y=1.08, x=0, font=dict(size=12, color="#cfd4ee")),
            xaxis=dict(showgrid=False, tickformat="%b" if gran == "Monthly" else "%d %b"),
            yaxis=dict(gridcolor="#1c2641", tickvals=tv, ticktext=tt, zeroline=False),
        )
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    with c2.container(key="card_channel"):
        st.markdown("<div class='title'>Channel Contribution</div><div class='muted'>In-Store vs Online split</div>", unsafe_allow_html=True)
        cm = m.channel_monthly(hist)
        last_months = sorted(cm["month"].unique())[-4:]
        cm = cm[cm["month"].isin(last_months)]
        chans = sorted(cm["channel"].unique())
        fig = go.Figure()
        for i, ch in enumerate(chans):
            d = cm[cm["channel"] == ch]
            fig.add_bar(x=[x.strftime("%b") for x in d["month"]], y=d["revenue"], name=ch, marker_color=[INDIGO, CYAN, AMBER][i % 3])
        fig.update_layout(
            barmode="group", bargap=0.35, height=260, margin=dict(l=0, r=0, t=6, b=0), showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#9aa3c7", size=11),
            xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#1c2641", showticklabels=False, zeroline=False),
            hoverlabel=dict(bgcolor="#1a2342", font_color="#fff"),
        )
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
        cs = m.channel_split(cur)
        mc = st.columns(max(len(cs), 1))
        for i, r in enumerate(cs.itertuples()):
            mc[i].markdown(
                f'<div class="mini"><span class="dot" style="background:{[INDIGO, CYAN, AMBER][i % 3]}"></span>'
                f'<span class="muted">{html.escape(r.channel)}</span><div class="amt">{inr(r.revenue)}</div>'
                f'<span class="muted">{r.share:.1f}% share · {r.orders} txns</span></div>', unsafe_allow_html=True)
    st.write("")

    # ---------------- products ----------------
    pt = m.product_table(cur)
    p1, p2 = st.columns([1, 1])
    with p1:
        top = pt.head(4)
        h = "<div class='card'><div style='display:flex;justify-content:space-between'><div class='title'>⭐ Top Selling Products</div>" \
            "<span class='muted' style='color:#a5a8ff'>View All SKUs →</span></div>"
        for i, r in enumerate(top.itertuples(), 1):
            w = r.revenue / top["revenue"].max() * 100
            h += (f"<div class='prow'><div class='top'><div><span class='num'>{i}</span><b>{html.escape(r.product_name)}</b></div>"
                  f"<b>{inr(r.revenue)}</b></div><div style='display:flex;justify-content:space-between;margin-left:32px' class='muted'>"
                  f"<span>{r.sku} · {int(r.units)} units sold</span><span class='green'>{r.margin_pct:.0f}% margin</span></div>"
                  f"<div class='bar-bg' style='margin-left:32px'><div class='bar-fg' style='width:{w:.0f}%'></div></div></div>")
        st.markdown(h + "</div>", unsafe_allow_html=True)
    with p2:
        att = m.attention_products(pt, **THR)
        h = f"<div class='card'><div class='title'>⚠️ Attention Required Products <span class='badge'>{len(att)} Low-Margin Items</span></div>"
        for r in att.head(4).to_dict("records"):
            tags = "".join(f"<span class='tag {c}'>{html.escape(t)}</span>" for t, c in r["tags"])
            h += (f"<div class='arow'><div><b>{html.escape(r['product_name'])}</b>{tags}<br>"
                  f"<span class='muted'>{r['sku']} · Revenue: {inr(r['revenue'])} · Margin: {r['margin_pct']:.1f}%</span></div>"
                  f"<span class='abtn'>{r['action']}</span></div>")
        if att.empty:
            h += "<p class='muted'>All products are healthy 🎉</p>"
        st.markdown(h + "</div>", unsafe_allow_html=True)
    st.write("")

    # ---------------- insights ----------------
    ins = m.insights(cur, hist)
    i1, i2, i3 = st.columns(3)
    if "peak_day" in ins:
        d, pct, h0, h1, wpct = ins["peak_day"]
        i1.markdown(
            f'<div class="icard"><div class="ihead"><div class="iicon" style="background:#14304a">⚡</div>'
            f'<span class="ilabel" style="color:{CYAN}">Revenue Opportunity</span></div>'
            f'<div class="ititle">Peak {d} Footfall Opportunity</div>'
            f'<div class="itext">{d}s bring {pct:.0f}% of your revenue, and {hr(h0)} – {hr(h1)} is the busiest window '
            f'({wpct:.0f}% of that day\'s sales). Instant combo bundles at that time could lift basket size.</div>'
            f'<div class="ibtn">View Peak Hour Breakdown →</div></div>', unsafe_allow_html=True)
    if "repeat" in ins:
        n, rev, pct = ins["repeat"]
        i2.markdown(
            f'<div class="icard"><div class="ihead"><div class="iicon" style="background:#12301f">🏷️</div>'
            f'<span class="ilabel" style="color:{GREEN}">Customer Retention</span></div>'
            f'<div class="ititle">Top Customer Loyalty Trend</div>'
            f'<div class="itext">Repeat customers accounted for <b>{inr(rev)}</b> ({pct:.0f}% of total revenue). '
            f'{n:,} customers have ordered more than once since {hist["date"].min():%b %Y}.</div>'
            f'<div class="ibtn">Setup Loyalty Campaign →</div></div>', unsafe_allow_html=True)
    if "velocity" in ins:
        name, x, units = ins["velocity"]
        i3.markdown(
            f'<div class="icard"><div class="ihead"><div class="iicon" style="background:#2a2140">📦</div>'
            f'<span class="ilabel" style="color:{PINK}">Supply Chain Watch</span></div>'
            f'<div class="ititle">Fastest-Moving Product</div>'
            f'<div class="itext"><b>{html.escape(name)}</b> is selling at <b>{x:.1f}x</b> its prior-30-day pace '
            f'({units} units in the last 30 days). Check stock levels before it runs out.</div>'
            f'<div class="ibtn primary">Review Stock →</div></div>', unsafe_allow_html=True)
    st.write("")

    # ---------------- transactions ----------------
    with st.container(key="card_tx"):
        a, b, c = st.columns([2.2, 2.2, 0.8], vertical_alignment="bottom")
        a.markdown("<div class='title'>Recent Live Transactions</div><div class='muted'>Synchronized omni-channel retail and online feed</div>", unsafe_allow_html=True)
        q = b.text_input("Search", placeholder="Search order ID, item...", label_visibility="collapsed")
        stat = st.segmented_control("Status", ["All", "Completed", "Processing", "Refunded"], default="All", key="stat", label_visibility="collapsed") or "All"
        tx = cur.sort_values("order_date", ascending=False)
        if stat != "All":
            tx = tx[tx["status"] == stat]
        if q:
            tx = tx[tx["order_id"].str.contains(q, case=False, regex=False) | tx["product_name"].str.contains(q, case=False, regex=False)]
        c.download_button("⬇ CSV", tx.drop(columns=["date"]).to_csv(index=False), "transactions.csv", mime="text/csv", width="stretch")
        rows = ""
        for r in tx.head(10).itertuples():
            icon = "🏬" if "store" in r.channel.lower() or "pos" in r.channel.lower() else "🌐"
            margin = r.profit / r.revenue * 100 if r.revenue else 0
            rows += (
                f"<tr><td style='color:#a5a8ff;font-weight:600'>#{html.escape(r.order_id)}</td>"
                f"<td><b>{html.escape(r.product_name)}</b> ×{int(r.quantity)}<br><span class='muted'>{r.sku} · {html.escape(r.category)}</span></td>"
                f"<td><span class='chan'>{icon} {html.escape(r.channel)}</span></td>"
                f"<td>{r.order_date:%d %b, %I:%M %p}</td><td><b>{inr(r.revenue)}</b></td>"
                f"<td><span class='green'>{inr(r.profit)}</span><br><span class='muted'>{margin:.1f}% margin</span></td>"
                f"<td><span class='pill {r.status.lower()}'>● {html.escape(r.status)}</span></td></tr>"
            )
        st.markdown(
            "<table class='tx'><thead><tr><th>Order ID</th><th>Items</th><th>Channel</th><th>Date & Time</th>"
            f"<th>Revenue</th><th>Profit & Margin</th><th>Status</th></tr></thead><tbody>{rows}</tbody></table>",
            unsafe_allow_html=True,
        )
        st.caption(f"Showing {min(10, len(tx))} of {len(tx):,} orders · All data shown is fictional demo data.")


elif page == "Sales Analytics":
    page_title("Sales Analytics", "How your sales behave by day, hour and category")
    ok = cur[~cur["is_refunded"]]
    a1, a2 = st.columns(2)
    with a1.container(key="card_sa1"):
        st.markdown("<div class='title'>Revenue by Weekday</div><div class='muted'>Your strongest day is highlighted</div>", unsafe_allow_html=True)
        wd = ok.groupby(ok["order_date"].dt.day_name())["revenue"].sum().reindex(DAYS, fill_value=0)
        fig = go.Figure(go.Bar(x=[d[:3] for d in wd.index], y=wd.values, marker_color=[CYAN if v == wd.max() else INDIGO for v in wd.values]))
        st.plotly_chart(dark(fig, 290), width="stretch", config=PLOT_CFG)
    with a2.container(key="card_sa2"):
        st.markdown("<div class='title'>Revenue & Profit by Category</div><div class='muted'>Which product groups earn the most</div>", unsafe_allow_html=True)
        cat = ok.groupby("category")[["revenue", "profit"]].sum().sort_values("revenue")
        fig = go.Figure()
        fig.add_bar(y=cat.index, x=cat["revenue"], orientation="h", name="Revenue", marker_color=INDIGO)
        fig.add_bar(y=cat.index, x=cat["profit"], orientation="h", name="Profit", marker_color=CYAN)
        fig.update_layout(barmode="group")
        st.plotly_chart(dark(fig, 290), width="stretch", config=PLOT_CFG)
    st.write("")
    with st.container(key="card_sa3"):
        st.markdown("<div class='title'>Busiest Hours</div><div class='muted'>Revenue by weekday and hour: brighter means more sales</div>", unsafe_allow_html=True)
        pv = ok.pivot_table(index=ok["order_date"].dt.day_name(), columns=ok["order_date"].dt.hour, values="revenue",
                            aggfunc="sum", fill_value=0).reindex(index=DAYS, columns=range(24), fill_value=0)
        fig = go.Figure(go.Heatmap(z=pv.values, x=[hr(h) for h in pv.columns], y=[d[:3] for d in pv.index],
                                   colorscale=[[0, "#111a2e"], [1, INDIGO]], showscale=False,
                                   hovertemplate="%{y} %{x}: ₹%{z:,.0f}<extra></extra>"))
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(dark(fig, 300), width="stretch", config=PLOT_CFG)
    st.write("")
    with st.container(key="card_sa4"):
        st.markdown("<div class='title'>Monthly Summary</div>", unsafe_allow_html=True)
        ps = m.periodic_series(hist, "MS")
        ps["Month"] = ps["order_date"].dt.strftime("%b %Y")
        ps["Margin"] = (ps["profit"] / ps["revenue"].where(ps["revenue"] != 0, 1) * 100).where(ps["revenue"] != 0, 0.0)
        st.dataframe(ps[["Month", "revenue", "profit", "orders", "aov", "Margin"]], hide_index=True, width="stretch",
                     column_config={"revenue": st.column_config.NumberColumn("Revenue", format="₹%d"),
                                    "profit": st.column_config.NumberColumn("Profit", format="₹%d"),
                                    "orders": "Orders", "aov": st.column_config.NumberColumn("Avg order", format="₹%d"),
                                    "Margin": st.column_config.NumberColumn("Margin", format="%.1f%%")})

elif page == "Product Performance":
    page_title("Product Performance", "Which products make money, and which ones leak profit")
    pt = m.product_table(cur)
    b1, b2 = st.columns(2)
    with b1.container(key="card_pp1"):
        st.markdown("<div class='title'>Volume vs Margin</div><div class='muted'>Bubble size = revenue · red = below your low-margin threshold</div>", unsafe_allow_html=True)
        fig = go.Figure(go.Scatter(
            x=pt["units"], y=pt["margin_pct"], mode="markers+text", text=[n.split(" (")[0][:20] for n in pt["product_name"]],
            textposition="top center", textfont=dict(size=10),
            marker=dict(size=pt["revenue"] / max(pt["revenue"].max(), 1) * 50 + 10, opacity=.8,
                        color=[RED if v < THR["margin_floor"] else GREEN for v in pt["margin_pct"]]),
            hovertemplate="%{text}<br>Units: %{x}<br>Margin: %{y:.1f}%<extra></extra>"))
        fig.update_xaxes(title="Units sold")
        fig.update_yaxes(title="Margin %")
        st.plotly_chart(dark(fig, 340), width="stretch", config=PLOT_CFG)
    with b2.container(key="card_pp2"):
        st.markdown("<div class='title'>Profit by Product</div><div class='muted'>Negative bars are products losing money</div>", unsafe_allow_html=True)
        pp = pt.sort_values("profit")
        fig = go.Figure(go.Bar(y=[n.split(" (")[0][:26] for n in pp["product_name"]], x=pp["profit"], orientation="h",
                               marker_color=[RED if v < 0 else CYAN for v in pp["profit"]]))
        st.plotly_chart(dark(fig, 340), width="stretch", config=PLOT_CFG)
    st.write("")
    with st.container(key="card_pp3"):
        st.markdown("<div class='title'>All Products</div>", unsafe_allow_html=True)
        st.dataframe(pt[["product_name", "sku", "units", "revenue", "profit", "margin_pct", "return_rate"]], hide_index=True, width="stretch",
                     column_config={"product_name": "Product", "sku": "SKU", "units": "Units sold",
                                    "revenue": st.column_config.NumberColumn("Revenue", format="₹%d"),
                                    "profit": st.column_config.NumberColumn("Profit", format="₹%d"),
                                    "margin_pct": st.column_config.NumberColumn("Margin", format="%.1f%%"),
                                    "return_rate": st.column_config.NumberColumn("Return rate", format="%.1f%%")})

elif page == "Data Management":
    page_title("Data Management", "What was loaded, what was fixed, and what your CSV needs to look like")
    d = st.columns(4)
    d[0].metric("Rows in file", f"{report['rows_raw']:,}")
    d[1].metric("Duplicates removed", report["duplicates_removed"])
    d[2].metric("Invalid rows removed", report["invalid_rows_removed"])
    d[3].metric("Clean rows used", f"{report['rows_clean']:,}")
    for _n in report["notes"]:
        st.info(_n)
    st.write("")
    e1, e2 = st.columns([1.2, 1])
    with e1.container(key="card_dm1"):
        st.markdown("<div class='title'>CSV format</div><div class='muted'>Use the Import CSV button at the top to upload your own file</div>", unsafe_allow_html=True)
        st.dataframe(pd.DataFrame({
            "Column (any similar name works)": ["order_date", "product_name", "unit_price OR total_sales", "quantity",
                                                "unit_cost OR total_profit", "order_id", "channel", "category",
                                                "status", "customer_id", "sku", "shipping_cost"],
            "Needed?": ["Yes", "Yes", "Yes (one of the two)", "No (1 per row if missing)", "No (needed for real profit)",
                        "No", "No", "No", "No", "No", "No", "No"],
            "What it is": ["Date (and time) of the sale", "Product sold", "Price per unit, or the line total",
                           "Units sold", "Cost per unit, or the profit of the line", "Order or bill number",
                           "In-Store / Online / segment", "Product group", "Completed / Refunded",
                           "Lets us find repeat customers", "Product code", "Delivery cost"]}), hide_index=True, width="stretch")
        template = pd.DataFrame([
            ["ORD-1", "2026-10-01 11:30:00", "Sample Product", 2, 250, 160, 0, "In-Store POS", "Snacks", "Completed", "CUST-1", "SKU-1"],
            ["ORD-2", "2026-10-01 15:10:00", "Sample Product", 1, 250, 160, 60, "Online Store", "Snacks", "Completed", "CUST-2", "SKU-1"]],
            columns=["order_id", "order_date", "product_name", "quantity", "unit_price", "unit_cost", "shipping_cost",
                     "channel", "category", "status", "customer_id", "sku"])
        st.download_button("⬇ Download CSV template", template.to_csv(index=False), "sales_template.csv", mime="text/csv")
    with e2.container(key="card_dm2"):
        st.markdown("<div class='title'>How cleaning works</div>", unsafe_allow_html=True)
        st.markdown(
            "- Column names are matched automatically (Qty, Rate, Item, Bill No...) and you can fix them\n"
            "- Repeated lines (same order, time and product) are dropped\n- Rows with a missing date, product, quantity or price are removed\n"
            "- Missing quantity = 1 per row; missing unit price = total sales / quantity\n"
            "- Missing costs are estimated from the product's median cost, or from a profit column\n"
            "- Refunded, returned and cancelled orders earn no revenue and no profit")
    st.write("")
    with st.container(key="card_dm3"):
        st.markdown("<div class='title'>Cleaned data preview</div><div class='muted'>First 50 rows after cleaning</div>", unsafe_allow_html=True)
        st.dataframe(df.drop(columns=["date"]).head(50), hide_index=True, width="stretch")

elif page == "Reports":
    page_title("Reports", f"Download a shareable summary for {start:%d %b %Y} – {end:%d %b %Y}")
    pt = m.product_table(cur)
    att = m.attention_products(pt, **THR)
    lines = [f"SALES SUMMARY: {BIZ}", f"Period: {start:%d %b %Y} to {end:%d %b %Y}", "",
             f"Revenue: {inr(S['revenue'])}", f"Profit: {inr(S['profit'])} ({S['margin']:.1f}% margin)",
             f"Orders: {S['orders']:,}   Average order value: {inr(S['aov'])}", "", "Top products by revenue:"]
    lines += [f"  {i}. {r.product_name} - {inr(r.revenue)} ({r.margin_pct:.0f}% margin)" for i, r in enumerate(pt.head(3).itertuples(), 1)]
    lines += ["", "Products needing attention:"]
    lines += [f"  - {r['product_name']}: {r['issue']} -> suggested: {r['action']}" for r in att.to_dict("records")] or ["  None"]
    text = "\n".join(lines)
    r1, r2 = st.columns([1.4, 1])
    with r1.container(key="card_rp1"):
        st.markdown("<div class='title'>Summary preview</div>", unsafe_allow_html=True)
        st.code(text, language=None)
    with r2.container(key="card_rp2"):
        st.markdown("<div class='title'>Downloads</div><div class='muted'>Share these with the shop owner</div>", unsafe_allow_html=True)
        st.write("")
        st.download_button("⬇ Full Excel report", build_report(), "localbiz_report.xlsx", width="stretch",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        st.download_button("⬇ Product table (CSV)", pt.to_csv(index=False), "products.csv", mime="text/csv", width="stretch")
        st.download_button("⬇ Text summary", text, "summary.txt", width="stretch")

elif page == "Settings":
    page_title("Settings", "Tune what counts as a problem product")
    with st.container(key="card_set"):
        bn = st.text_input("Business name", value=st.session_state.get("biz_name", ""), placeholder="e.g. Sharma General Store", key="_bn").strip()
        if bn != st.session_state.get("biz_name", ""):
            st.session_state["biz_name"] = bn
            st.rerun()
        mf = st.number_input("Low-margin threshold (%)", 0.0, 50.0, float(st.session_state.get("margin_floor", 10)), 1.0, key="_mf")
        rc = st.number_input("High return-rate threshold (%)", 0.0, 50.0, float(st.session_state.get("return_ceiling", 7)), 0.5, key="_rc")
        st.session_state["margin_floor"], st.session_state["return_ceiling"] = mf, rc
        st.caption("These control the Attention Required list on Overview, the charts on Product Performance and the exported report. "
                   "The revenue target is set in the ⚙ menu at the top.")