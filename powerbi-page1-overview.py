# -*- coding: utf-8 -*-
# ======================================================================
# Olist E-Commerce — Power BI Python visual · PAGE 1: Overview (نظرة عامة)
# ======================================================================
# REQUIRED — drag EXACTLY these 7 columns into the Python visual's
# "Values" well before pasting this script:
# المطلوب — اسحب هذه الأعمدة السبعة بالضبط إلى خانة Values في الفيجوال:
#
#   1) order_id
#   2) order_item_id          (keeps item-level rows distinct)
#   3) order_purchase_timestamp
#   4) price
#   5) payment_type
#   6) customer_state
#   7) customer_unique_id
#
# All 6 columns must come from ONE flat table (see powerbi-guide.md for the
# quick Power Query merge that builds it — the Python visual only accepts
# fields that arrive together as the injected `dataset` DataFrame).
# Build the flat table starting from `orders` with LEFT joins so every order
# is kept (orders without item lines get price = 0, handled below).
# كل الأعمدة لازم تكون من جدول واحد مسطّح (FlatSales) — الطريقة في powerbi-guide.md.
#
# RULES: this script uses ONLY the injected `dataset` DataFrame —
# no file loading, no hard-coded paths, no plt.show().
# Power BI renders the returned figure automatically.
# ======================================================================

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyBboxPatch

REQUIRED_COLS = [
    "order_id",
    "order_item_id",
    "order_purchase_timestamp",
    "price",
    "payment_type",
    "customer_state",
    "customer_unique_id",
]

missing = [c for c in REQUIRED_COLS if c not in dataset.columns]
if missing:
    raise ValueError(
        "Missing columns in the Python visual's Values well: "
        + ", ".join(missing)
        + ". Drag all 7 listed columns (see header) into Values and re-run."
    )

# ---- palette ----
INDIGO = "#4338CA"
INDIGO_DARK = "#312E81"
INDIGO_MID = "#6366F1"
INDIGO_LIGHT = "#818CF8"
INDIGO_PALE = "#C7D2FE"
AMBER = "#F59E0B"
AMBER_DARK = "#D97706"
BG = "#F7F6FE"
PANEL_EDGE = "#E4E1FB"
GRID = "#EDEBFA"
TEXT = "#1E1B4B"
GRAY = "#6B7280"

# ---------------- prepare ----------------
df = dataset.copy()
df["order_purchase_timestamp"] = pd.to_datetime(
    df["order_purchase_timestamp"], errors="coerce"
)
df = df.dropna(subset=["order_id", "order_purchase_timestamp"])
df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0.0)

n_orders = df["order_id"].nunique()
n_customers = df["customer_unique_id"].nunique()
total_rev = df["price"].sum()
avg_ticket = total_rev / n_orders if n_orders else 0
ref = df["order_purchase_timestamp"].max()

# monthly trend
df["month"] = df["order_purchase_timestamp"].dt.to_period("M")
mo_orders = df.groupby("month")["order_id"].nunique()
mo_rev = df.groupby("month")["price"].sum()
mo_idx = mo_orders.index.to_timestamp()

# payment mix (one row per order)
pay = (
    df.drop_duplicates("order_id")["payment_type"]
    .value_counts(normalize=True)
)
pay = pay[pay.index != "not_defined"]

# ---------------- figure ----------------
plt.rcParams.update(
    {"font.size": 11, "axes.titlesize": 13, "axes.titleweight": "bold"}
)
fig = plt.figure(figsize=(16, 10))
fig.patch.set_facecolor(BG)
gs = fig.add_gridspec(
    3, 3, height_ratios=[0.62, 1.15, 1.0],
    hspace=0.9, wspace=0.35, left=0.07, right=0.97, top=0.88, bottom=0.08,
)

fig.suptitle("Olist E-Commerce — Executive Overview",
             fontsize=17, fontweight="bold", color=INDIGO_DARK, y=0.97)
fig.text(0.5, 0.93, "Page 1 · KPIs, monthly trend, payment mix & top states",
         ha="center", fontsize=11, color=GRAY)
fig.text(0.5, 0.02, f"Power BI Python visual  |  Reference date: {ref.date()}  |  "
                    "Currency: Brazilian real (R$)",
         ha="center", fontsize=9, color=GRAY)


def style_ax(ax):
    ax.set_facecolor("white")
    for s in ax.spines.values():
        s.set_color(PANEL_EDGE)
    ax.title.set_color(INDIGO_DARK)
    ax.yaxis.grid(True, color=GRID, linewidth=0.7, linestyle="--")
    ax.set_axisbelow(True)


# ---- KPI cards (rounded) ----
kax = fig.add_subplot(gs[0, :])
kax.axis("off")
kax.set_xlim(0, 1)
kax.set_ylim(0, 1)
kpis = [
    ("ORDERS", f"{n_orders:,}"),
    ("UNIQUE CUSTOMERS", f"{n_customers:,}"),
    ("TOTAL REVENUE", f"R$ {total_rev/1e6:.2f}M"),
    ("AVG TICKET", f"R$ {avg_ticket:,.2f}"),
]
for i, (label, value) in enumerate(kpis):
    x0 = 0.008 + i * 0.25
    card = FancyBboxPatch(
        (x0, 0.04), 0.234, 0.92,
        boxstyle="round,pad=0.012,rounding_size=0.045",
        facecolor="white", edgecolor=PANEL_EDGE, linewidth=1.4,
        transform=kax.transAxes,
    )
    kax.add_patch(card)
    kax.plot([x0 + 0.028, x0 + 0.078], [0.40, 0.40], color=AMBER,
             linewidth=5, solid_capstyle="round",
             transform=kax.transAxes, clip_on=False)
    kax.text(x0 + 0.117, 0.66, value, fontsize=21, fontweight="bold",
             color=INDIGO_DARK, ha="center", va="center",
             transform=kax.transAxes)
    kax.text(x0 + 0.117, 0.24, label, fontsize=9.5, color=GRAY,
             ha="center", va="center", transform=kax.transAxes)

# ---- monthly trend (wide) ----
ax = fig.add_subplot(gs[1, 0:2])
style_ax(ax)
ax.bar(mo_idx, mo_orders.values, width=22, color=INDIGO_PALE,
       edgecolor="white", label="Orders", zorder=3)
ax2 = ax.twinx()
ax2.plot(mo_idx, mo_rev.values / 1e3, color=AMBER_DARK, linewidth=2.8,
         marker="o", markersize=4, markerfacecolor=AMBER,
         markeredgecolor="white", label="Revenue", zorder=4)
ax2.spines["top"].set_visible(False)
ax.set_title("Monthly Orders & Revenue", pad=10)
ax.set_ylabel("Orders", color=INDIGO_MID)
ax2.set_ylabel("Revenue (R$ thousands)", color=AMBER_DARK)
ax.tick_params(axis="x", rotation=30, labelsize=8.5)
h1, l1 = ax.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=10, frameon=False)

# ---- payment donut ----
ax = fig.add_subplot(gs[1, 2])
style_ax(ax)
ax.yaxis.grid(False)
pcolors = [INDIGO, INDIGO_LIGHT, AMBER, INDIGO_PALE]
wedges, _, autotexts = ax.pie(
    pay.values, colors=pcolors[: len(pay)], startangle=90,
    autopct=lambda p: f"{p:.1f}%" if p >= 5 else "",
    pctdistance=0.78,
    wedgeprops=dict(width=0.40, edgecolor="white", linewidth=2),
)
for t in autotexts:
    t.set_fontsize(9.5)
    t.set_color(TEXT)
    t.set_weight("bold")
ax.legend(wedges, pay.index.str.replace("_", " ").str.title(),
          loc="center", bbox_to_anchor=(0.5, -0.16), ncol=2,
          fontsize=10, frameon=False)
ax.set_title("Payment-Type Mix", pad=10)

# ---- top states (fills the remaining space) ----
ax = fig.add_subplot(gs[2, :])
style_ax(ax)
st_rev = df.groupby("customer_state")["price"].sum().sort_values(ascending=False).head(8)
bars = ax.bar(st_rev.index, st_rev.values / 1e3, color=INDIGO,
              edgecolor="white", width=0.6, zorder=3)
ax.set_title("Top-8 States by Revenue", pad=10)
ax.set_ylabel("Revenue (R$ thousands)")
ax.set_xlabel("Customer state")
for b, v in zip(bars, st_rev.values):
    ax.text(b.get_x() + b.get_width() / 2, v / 1e3 + 6, f"{v/1e3:,.0f}k",
            ha="center", va="bottom", fontsize=9, color=TEXT, weight="bold")

# NOTE: no plt.show() — Power BI renders this figure automatically.
