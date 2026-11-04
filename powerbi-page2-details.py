# -*- coding: utf-8 -*-
# ======================================================================
# Olist E-Commerce — Power BI Python visual · PAGE 2: Details (التفاصيل)
# ======================================================================
# REQUIRED — drag EXACTLY these 6 columns into the Python visual's
# "Values" well before pasting this script:
# المطلوب — اسحب هذه الأعمدة الستة بالضبط إلى خانة Values في الفيجوال:
#
#   1) order_id
#   2) order_item_id          (keeps item-level rows distinct)
#   3) order_purchase_timestamp
#   4) price
#   5) product_category_name_english
#   6) customer_unique_id
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

REQUIRED_COLS = [
    "order_id",
    "order_item_id",
    "order_purchase_timestamp",
    "price",
    "product_category_name_english",
    "customer_unique_id",
]

missing = [c for c in REQUIRED_COLS if c not in dataset.columns]
if missing:
    raise ValueError(
        "Missing columns in the Python visual's Values well: "
        + ", ".join(missing)
        + ". Drag all 6 listed columns (see header) into Values and re-run."
    )

# ---- palette ----
INDIGO = "#4338CA"
INDIGO_DARK = "#312E81"
INDIGO_MID = "#6366F1"
BG = "#F7F6FE"
PANEL_EDGE = "#E4E1FB"
GRID = "#EDEBFA"
TEXT = "#1E1B4B"
GRAY = "#6B7280"
AMBER = "#F59E0B"
AMBER_LIGHT = "#FBBF24"
CHURN_DAYS = 180

# ---------------- prepare ----------------
df = dataset.copy()
df["order_purchase_timestamp"] = pd.to_datetime(
    df["order_purchase_timestamp"], errors="coerce"
)
df = df.dropna(subset=["order_id", "order_purchase_timestamp"])
df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0.0)
df["product_category_name_english"] = df[
    "product_category_name_english"
].fillna("Other")

# ---------------- RFM ----------------
ref = df["order_purchase_timestamp"].max()
g = df.groupby("customer_unique_id")
recency = (ref - g["order_purchase_timestamp"].max()).dt.days
frequency = g["order_id"].nunique()
monetary = g["price"].sum()
rfm = pd.DataFrame(
    {"recency": recency, "frequency": frequency, "monetary": monetary}
)
p80 = rfm["monetary"].quantile(0.80)


def _seg(r):
    if r["frequency"] >= 2 and r["monetary"] >= p80:
        return "Champions"
    if r["frequency"] >= 2:
        return "Loyal"
    if r["recency"] <= 90:
        return "New"
    if r["recency"] <= 365:
        return "At-Risk"
    return "Lost"


rfm["segment"] = rfm.apply(_seg, axis=1)
seg_order = ["Champions", "Loyal", "New", "At-Risk", "Lost"]
seg_counts = rfm["segment"].value_counts().reindex(seg_order, fill_value=0)

churn = (
    (rfm["recency"] > CHURN_DAYS)
    .groupby(rfm["segment"])
    .mean()
    .reindex(["Champions", "Loyal", "New", "At-Risk"])
    * 100
)

# ---------------- top categories ----------------
cat_rev = (
    df.groupby("product_category_name_english")["price"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
)

# ---------------- cohort retention ----------------
first = g["order_purchase_timestamp"].min()
df["cohort"] = df["customer_unique_id"].map(first).dt.to_period("M")
df["ord_m"] = df["order_purchase_timestamp"].dt.to_period("M")
df["m_since"] = (df["ord_m"].astype(int) - df["cohort"].astype(int)).astype(int)
cohort_list = sorted(df["cohort"].dropna().unique())[-13:-1]
coh = (
    df[df["cohort"].isin(cohort_list) & df["m_since"].between(0, 11)]
    .groupby(["cohort", "m_since"])["customer_unique_id"]
    .nunique()
    .unstack(fill_value=0)
)
coh_ret = coh.divide(coh[0], axis=0) * 100

# ---------------- figure ----------------
plt.rcParams.update(
    {"font.size": 11, "axes.titlesize": 13, "axes.titleweight": "bold"}
)
fig = plt.figure(figsize=(16, 10))
fig.patch.set_facecolor(BG)
gs = fig.add_gridspec(
    2, 2, hspace=0.55, wspace=0.30,
    left=0.07, right=0.97, top=0.88, bottom=0.08,
)

fig.suptitle("Olist E-Commerce — Customer Details",
             fontsize=17, fontweight="bold", color=INDIGO_DARK, y=0.97)
fig.text(0.5, 0.93, "Page 2 · RFM segments, churn, categories & cohort retention",
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


# ---- RFM segments ----
ax = fig.add_subplot(gs[0, 0])
style_ax(ax)
seg_colors = [INDIGO_DARK, INDIGO_MID, AMBER, AMBER_LIGHT, "#94A3B8"]
bars = ax.bar(seg_counts.index, seg_counts.values, color=seg_colors,
              edgecolor="white", width=0.62, zorder=3)
ax.set_title("RFM Customer Segments", pad=10)
ax.set_ylabel("Customers")
ax.tick_params(axis="x", rotation=18, labelsize=9)
for b, v in zip(bars, seg_counts.values):
    ax.text(b.get_x() + b.get_width() / 2,
            b.get_height() + seg_counts.max() * 0.03,
            f"{v:,}", ha="center", va="bottom", fontsize=9.5,
            color=TEXT, weight="bold")

# ---- churn by segment ----
ax = fig.add_subplot(gs[0, 1])
style_ax(ax)
cc = [INDIGO_DARK, INDIGO_MID, AMBER, AMBER_LIGHT]
bars = ax.bar(churn.index, churn.values, color=cc, edgecolor="white",
              width=0.58, zorder=3)
ax.set_title(f"Churn by Segment (no order in last {CHURN_DAYS} days)", pad=10)
ax.set_ylabel("Churn rate %")
ax.tick_params(axis="x", rotation=18, labelsize=9)
ax.set_ylim(0, 105)
for b, v in zip(bars, churn.values):
    ax.text(b.get_x() + b.get_width() / 2, v + 1.5, f"{v:.1f}%",
            ha="center", va="bottom", fontsize=9.5, color=TEXT, weight="bold")

# ---- top categories ----
ax = fig.add_subplot(gs[1, 0])
style_ax(ax)
labels = cat_rev.index.str.replace("_", " ").str.title()[::-1]
vals = cat_rev.values[::-1]
bars = ax.barh(labels, vals / 1e3, color=INDIGO, edgecolor="white",
               height=0.62, zorder=3)
ax.set_title("Top-10 Categories by Revenue", pad=10)
ax.set_xlabel("Revenue (R$ thousands)")
ax.tick_params(axis="y", labelsize=8.5)
for b, v in zip(bars, vals):
    ax.text(v / 1e3 + 4, b.get_y() + b.get_height() / 2, f"{v/1e3:,.0f}k",
            va="center", fontsize=8, color=GRAY)

# ---- cohort heatmap ----
ax = fig.add_subplot(gs[1, 1])
ax.set_facecolor("white")
for s in ax.spines.values():
    s.set_color(PANEL_EDGE)
ax.title.set_color(INDIGO_DARK)
data = coh_ret.values
im = ax.imshow(data, aspect="auto", cmap="Purples", vmin=0, vmax=100)
ax.set_xticks(range(data.shape[1]))
ax.set_xticklabels([f"m{m}" for m in range(data.shape[1])], fontsize=8)
ax.set_yticks(range(data.shape[0]))
ax.set_yticklabels([str(c) for c in coh_ret.index], fontsize=8)
ax.set_xlabel("Months since first purchase")
ax.set_ylabel("Cohort")
ax.set_title("Cohort Retention (% ordering in month m)", pad=10)
for i in range(data.shape[0]):
    for j in range(data.shape[1]):
        v = data[i, j]
        ax.text(j, i, f"{v:.1f}", ha="center", va="center",
                fontsize=6.5, color="white" if v > 40 else TEXT)
cb = fig.colorbar(im, ax=ax, shrink=0.92, pad=0.02)
cb.set_label("% retained", fontsize=8.5)
cb.ax.tick_params(labelsize=8)
cb.outline.set_edgecolor(PANEL_EDGE)

# NOTE: no plt.show() — Power BI renders this figure automatically.
