"""Download the Olist Brazilian E-Commerce public dataset and apply a
deterministic sample (seed 42 -> 30,000 orders), saving sampled tables to data/.

Dataset: Olist Brazilian E-Commerce (orders, customers, items, payments,
products + category translation). Source mirror:
https://github.com/olist/work-at-olist-data  (dataset published by Olist).

Run:  python download_data.py
"""

import os
import urllib.request

BASE_URL = (
    "https://raw.githubusercontent.com/olist/work-at-olist-data/master/datasets/"
)
FILES = [
    "olist_orders_dataset.csv",
    "olist_customers_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_products_dataset.csv",
    "product_category_name_translation.csv",
]
OUT_NAMES = [
    "orders.csv",
    "customers.csv",
    "order_items.csv",
    "order_payments.csv",
    "products.csv",
    "product_category_name_translation.csv",
]

SEED = 42
N_ORDERS = 30_000


def main() -> None:
    import pandas as pd  # noqa: PLC0415 - only needed when actually running

    here = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(here, "data")
    os.makedirs(data_dir, exist_ok=True)
    tmp_dir = os.path.join(here, ".download_tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    # 1) Download the 6 source CSVs
    for fname in FILES:
        url = BASE_URL + fname
        dest = os.path.join(tmp_dir, fname)
        print(f"Downloading {fname} ...")
        urllib.request.urlretrieve(url, dest)

    # 2) Deterministic sample: 30,000 orders with seed 42
    orders = pd.read_csv(os.path.join(tmp_dir, FILES[0]))
    print(f"Source orders: {len(orders)} -> sampling {N_ORDERS} with seed {SEED}")
    sampled_orders = orders.sample(n=N_ORDERS, random_state=SEED).copy()
    order_ids = set(sampled_orders.order_id)
    customer_ids = set(sampled_orders.customer_id)

    customers = pd.read_csv(os.path.join(tmp_dir, FILES[1]))
    customers = customers[customers.customer_id.isin(customer_ids)].copy()

    items = pd.read_csv(os.path.join(tmp_dir, FILES[2]))
    items = items[items.order_id.isin(order_ids)].copy()

    payments = pd.read_csv(os.path.join(tmp_dir, FILES[3]))
    payments = payments[payments.order_id.isin(order_ids)].copy()

    products = pd.read_csv(os.path.join(tmp_dir, FILES[4]))
    products = products[products.product_id.isin(set(items.product_id))].copy()

    translation = pd.read_csv(os.path.join(tmp_dir, FILES[5]))

    # 3) Save
    for df, name in zip(
        [sampled_orders, customers, items, payments, products, translation],
        OUT_NAMES,
    ):
        path = os.path.join(data_dir, name)
        df.to_csv(path, index=False)
        print(f"  saved {name}: {df.shape[0]} rows x {df.shape[1]} cols")

    print("Done.")


if __name__ == "__main__":
    main()
