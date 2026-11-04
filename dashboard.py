"""Olist Brazilian E-Commerce Customer Analytics dashboard.

Reads the sampled dataset from data/ (see download_data.py) and renders
dashboard.png at 1600x1000 px. Design: indigo (#4338CA) + amber (#F59E0B)
on a light background, rounded KPI cards, asymmetric panel layout.
Run:  python dashboard.py
"""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "dashboard.png")

CHURN_DAYS = 180  # churned = no order in the final 180 days of the dataset

# ---- palette ----
INDIGO = "#4338CA"
INDIGO_DARK = "#312E81"
INDIGO_MID = "#6366F1"
INDIGO_LIGHT = "#818CF8"
INDIGO_PALE = "#C7D2FE"
AMBER = "#F59E0B"
AMBER_DARK = "#D97706"
AMBER_LIGHT = "#FBBF24"
BG = "#F7F6FE"
PANEL_EDGE = "#E4E1FB"
GRID = "#EDEBFA"
TEXT = "#1E1B4B"
GRAY = "#6B7280"


def load():
    orders = pd.read_csv(
        os.path.join(DATA, "orders.csv"),
        parse_dates=[
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
    )
    customers = pd.read_csv(os.path.join(DATA, "customers.csv"))
    items = pd.read_csv(os.path.join(DATA, "order_items.csv"))
    payments = pd.read_csv(os.path.join(DATA, "order_payments.csv"))
    products = pd.read_csv(os.path.join(DATA, "products.csv"))
    trans = pd.read_csv(os.path.join(DATA, "product_category_name_translation.csv"))
    return orders, customers, items, payments, products, trans


def rfm_segments(orders, customers, items):
    rev = items.groupby("order_id")["price"].sum().rename("rev")
    o = (
        orders.merge(customers[["customer_id", "customer_unique_id"]], on="customer_id")
        .merge(rev, on="order_id", how="left")
    )
    ref = o["order_purchase_timestamp"].max()
    rfm = o.groupby("customer_unique_id").agg(
        recency=(
            "order_purchase_timestamp",
            lambda x: (ref - x.max()).days,
        ),
        frequency=("order_id", "nunique"),
        monetary=("rev", "sum"),
    )
    p80 = rfm["monetary"].quantile(0.80)

    def seg(r):
        if r["frequency"] >= 2 and r["monetary"] >= p80:
            return "Champions"
        if r["frequency"] >= 2:
            return "Loyal"
        if r["recency"] <= 90:
            return "New"
        if r["recency"] <= 365:
            return "At-Risk"
        return "Lost"

    rfm["segment"] = rfm.apply(seg, axis=1)
    return rfm, ref


def style_ax(ax):
    ax.set_facecolor("white")
    for s in ax.spines.values():
        s.set_color(PANEL_EDGE)
    ax.title.set_color(INDIGO_DARK)
    ax.yaxis.grid(True, color=GRID, linewidth=0.7, linestyle="--")
    ax.set_axisbelow(True)


def main():
    orders, customers, items, payments, products, trans = load()
    rfm, ref_date = rfm_segments(orders, customers, items)

    # ---------- derived facts ----------
    n_orders = len(orders)
    n_customers = rfm.shape[0]
    order_rev = items.groupby("order_id")["price"].sum()
    total_rev = order_rev.sum()
    avg_ticket = total_rev / n_orders

    monthly = orders.copy()
    monthly["month"] = monthly["order_purchase_timestamp"].dt.to_period("M")
    mo_orders = monthly.groupby("month").size()
    mo_rev = order_rev.reindex(orders["order_id"]).groupby(
        monthly["month"].values
    ).sum()
    mo_rev = pd.Series(mo_rev.values, index=mo_orders.index)
    mo_idx = pd.PeriodIndex(mo_orders.index, freq="M").to_timestamp()

    seg_order = ["Champions", "Loyal", "New", "At-Risk", "Lost"]
    seg_counts = rfm["segment"].value_counts().reindex(seg_order, fill_value=0)

    pay = payments["payment_type"].value_counts(normalize=True)
    pay = pay[pay.index != "not_defined"]

    ip = (
        items.merge(products[["product_id", "product_category_name"]], on="product_id", how="left")
        .merge(trans, on="product_category_name", how="left")
    )
    ip["cat_en"] = ip["product_category_name_english"].fillna("other")
    cat_rev = ip.groupby("cat_en")["price"].sum().sort_values(ascending=False).head(10)

    # cohorts: first-purchase month x months since first purchase
    c = orders.merge(customers[["customer_id", "customer_unique_id"]], on="customer_id")
    first = c.groupby("customer_unique_id")["order_purchase_timestamp"].min()
    c["cohort"] = c["customer_unique_id"].map(first).dt.to_period("M")
    c["ord_m"] = c["order_purchase_timestamp"].dt.to_period("M")
    c["m_since"] = (c["ord_m"].astype(int) - c["cohort"].astype(int)).astype(int)
    cohort_list = sorted(c["cohort"].dropna().unique())[-13:-1]  # last 12 full cohorts
    coh = (
        c[c["cohort"].isin(cohort_list) & c["m_since"].between(0, 11)]
        .groupby(["cohort", "m_since"])["customer_unique_id"]
        .nunique()
        .unstack(fill_value=0)
    )
    coh_ret = coh.divide(coh[0], axis=0) * 100

    # churn by segment (Lost = 100% by definition -> excluded)
    churn = (
        (rfm["recency"] > CHURN_DAYS)
        .groupby(rfm["segment"])
        .mean()
        .reindex(["Champions", "Loyal", "New", "At-Risk"])
        * 100
    )

    # ---------- figure ----------
    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.titleweight": "bold",
            "axes.labelsize": 10,
            "font.family": "sans-serif",
        }
    )
    fig = plt.figure(figsize=(16, 10), dpi=100)
    fig.patch.set_facecolor(BG)
    gs = fig.add_gridspec(
        4, 3,
        height_ratios=[0.62, 1.05, 1.0, 1.05],
        hspace=0.85, wspace=0.35,
        left=0.075, right=0.97, top=0.90, bottom=0.07,
    )

    fig.suptitle(
        "Olist Brazilian E-Commerce — Customer Analytics",
        fontsize=17, fontweight="bold", color=INDIGO_DARK, y=0.975,
    )
    fig.text(
        0.5, 0.945,
        "Real orders from the Olist marketplace, Brazil  •  sampled n=30,000 orders (seed 42)",
        ha="center", fontsize=10.5, color=GRAY,
    )
    fig.text(
        0.5, 0.015,
        "Source: Olist Brazilian E-Commerce public dataset (github.com/olist/work-at-olist-data)  |  "
        f"Reference date: {ref_date.date()}  |  Currency: Brazilian real (R$)",
        ha="center", fontsize=8.5, color=GRAY,
    )

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
        # amber accent dash
        kax.plot(
            [x0 + 0.028, x0 + 0.078], [0.40, 0.40],
            color=AMBER, linewidth=5, solid_capstyle="round",
            transform=kax.transAxes, clip_on=False,
        )
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
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))
    ax.tick_params(axis="x", rotation=30, labelsize=8)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=9, frameon=False)

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
        t.set_fontsize(9)
        t.set_color(TEXT)
        t.set_weight("bold")
    ax.legend(wedges, pay.index.str.replace("_", " ").str.title(),
              loc="center", bbox_to_anchor=(0.5, -0.14), ncol=2,
              fontsize=9, frameon=False)
    ax.set_title("Payment-Type Mix", pad=10)

    # ---- RFM segments ----
    ax = fig.add_subplot(gs[2, 0])
    style_ax(ax)
    seg_colors = [INDIGO_DARK, INDIGO_MID, AMBER, AMBER_LIGHT, "#94A3B8"]
    bars = ax.bar(seg_counts.index, seg_counts.values, color=seg_colors,
                  edgecolor="white", width=0.66, zorder=3)
    ax.set_title("RFM Customer Segments", pad=10)
    ax.set_ylabel("Customers")
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))
    ax.tick_params(axis="x", rotation=18, labelsize=8.5)
    for b, v in zip(bars, seg_counts.values):
        ax.text(b.get_x() + b.get_width() / 2,
                b.get_height() + seg_counts.max() * 0.02,
                f"{v:,}", ha="center", va="bottom", fontsize=8.5,
                color=TEXT, weight="bold")

    # ---- top categories ----
    ax = fig.add_subplot(gs[2, 1])
    style_ax(ax)
    labels = cat_rev.index.str.replace("_", " ").str.title()[::-1]
    vals = cat_rev.values[::-1]
    bars = ax.barh(labels, vals / 1e3, color=INDIGO, edgecolor="white",
                   height=0.62, zorder=3)
    ax.set_title("Top-10 Categories by Revenue", pad=10)
    ax.set_xlabel("Revenue (R$ thousands)")
    ax.tick_params(axis="y", labelsize=8)
    ax.xaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))
    for b, v in zip(bars, vals):
        ax.text(v / 1e3 + 4, b.get_y() + b.get_height() / 2, f"{v/1e3:,.0f}k",
                va="center", fontsize=7.5, color=GRAY)

    # ---- churn by segment ----
    ax = fig.add_subplot(gs[2, 2])
    style_ax(ax)
    cc = [INDIGO_DARK, INDIGO_MID, AMBER, AMBER_LIGHT]
    bars = ax.bar(churn.index, churn.values, color=cc, edgecolor="white",
                  width=0.62, zorder=3)
    ax.set_title(f"Churn by Segment\n(no order in last {CHURN_DAYS} days)", pad=10)
    ax.set_ylabel("Churn rate %")
    ax.tick_params(axis="x", rotation=18, labelsize=8.5)
    ax.set_ylim(0, 105)
    for b, v in zip(bars, churn.values):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.5, f"{v:.1f}%",
                ha="center", va="bottom", fontsize=8.5, color=TEXT,
                weight="bold")

    # ---- cohort heatmap (full width) ----
    ax = fig.add_subplot(gs[3, :])
    ax.set_facecolor("white")
    for s in ax.spines.values():
        s.set_color(PANEL_EDGE)
    ax.title.set_color(INDIGO_DARK)
    data = coh_ret.values
    im = ax.imshow(data, aspect="auto", cmap="Purples", vmin=0, vmax=100)
    ax.set_xticks(range(data.shape[1]))
    ax.set_xticklabels([f"m{m}" for m in range(data.shape[1])], fontsize=8.5)
    ax.set_yticks(range(data.shape[0]))
    ax.set_yticklabels([str(c) for c in coh_ret.index], fontsize=8.5)
    ax.set_xlabel("Months since first purchase")
    ax.set_ylabel("Cohort (first-purchase month)")
    ax.set_title("Cohort Retention — % of cohort ordering in month m", pad=10)
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            v = data[i, j]
            ax.text(j, i, f"{v:.1f}", ha="center", va="center",
                    fontsize=7, color="white" if v > 40 else TEXT)
    cb = fig.colorbar(im, ax=ax, shrink=0.92, pad=0.012)
    cb.set_label("% retained", fontsize=8.5)
    cb.ax.tick_params(labelsize=8)
    cb.outline.set_edgecolor(PANEL_EDGE)

    fig.savefig(OUT)
    print(f"Saved {OUT} ({os.path.getsize(OUT):,} bytes)")
    print(f"KPIs: orders={n_orders:,} customers={n_customers:,} "
          f"revenue=R${total_rev:,.2f} avg_ticket=R${avg_ticket:,.2f}")


if __name__ == "__main__":
    main()
