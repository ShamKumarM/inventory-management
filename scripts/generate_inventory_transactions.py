import random

import numpy as np
import pandas as pd

from src.config import (
    SYNTHETIC_DIR,
    RANDOM_SEED,
)

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


def generate_inventory_transactions():

    print("Loading datasets...")

    products = pd.read_csv(
        SYNTHETIC_DIR / "products.csv"
    )

    orders = pd.read_csv(
        SYNTHETIC_DIR / "orders.csv"
    )

    order_items = pd.read_csv(
        SYNTHETIC_DIR / "order_items.csv"
    )

    warehouses = pd.read_csv(
        SYNTHETIC_DIR / "warehouses.csv"
    )

    # -----------------------------------------
    # Delivered orders only create sales
    # -----------------------------------------

    delivered_orders = orders[
        orders["order_status"] == "delivered"
    ][
        [
            "order_id",
            "order_date",
        ]
    ]

    sales = order_items.merge(
        delivered_orders,
        on="order_id",
        how="inner",
    )

    # -----------------------------------------
    # Assign warehouse
    # -----------------------------------------

    warehouse_ids = warehouses[
        "warehouse_id"
    ].tolist()

    sales["warehouse_id"] = np.random.choice(
        warehouse_ids,
        size=len(sales),
    )

    sales_transactions = pd.DataFrame(
        {
            "transaction_id": [
                f"TXN-SALE-{i:08d}"
                for i in range(
                    1,
                    len(sales) + 1,
                )
            ],
            "product_id": sales[
                "product_id"
            ],
            "warehouse_id": sales[
                "warehouse_id"
            ],
            "transaction_type": "SALE",
            "quantity": sales[
                "quantity"
            ],
            "transaction_date": sales[
                "order_date"
            ],
            "reference_id": sales[
                "order_id"
            ],
        }
    )

    # -----------------------------------------
    # Generate purchases
    # -----------------------------------------

    start_date = pd.to_datetime(
        orders["order_date"].min()
    )

    end_date = pd.to_datetime(
        orders["order_date"].max()
    )

    purchase_records = []

    transaction_counter = 1

    for _, product in products.iterrows():

        # Generate periodic purchase events
        purchase_dates = pd.date_range(
            start=start_date,
            end=end_date,
            freq="14D",
        )

        for purchase_date in purchase_dates:

            warehouse_id = random.choice(
                warehouse_ids
            )

            quantity = random.randint(
                500,
                3000,
            )

            purchase_records.append(
                {
                    "transaction_id":
                        f"TXN-PURCHASE-"
                        f"{transaction_counter:08d}",

                    "product_id":
                        product["product_id"],

                    "warehouse_id":
                        warehouse_id,

                    "transaction_type":
                        "PURCHASE",

                    "quantity":
                        quantity,

                    "transaction_date":
                        purchase_date,

                    "reference_id":
                        None,
                }
            )

            transaction_counter += 1

    purchase_transactions = pd.DataFrame(
        purchase_records
    )

    # -----------------------------------------
    # Generate returns
    # -----------------------------------------

    return_count = int(
        len(sales) * 0.03
    )

    return_samples = sales.sample(
        return_count,
        random_state=RANDOM_SEED,
    )

    return_transactions = pd.DataFrame(
        {
            "transaction_id": [
                f"TXN-RETURN-{i:08d}"
                for i in range(
                    1,
                    len(return_samples) + 1,
                )
            ],
            "product_id":
                return_samples["product_id"],
            "warehouse_id":
                return_samples["warehouse_id"],
            "transaction_type":
                "RETURN",
            "quantity":
                return_samples["quantity"],
            "transaction_date":
                return_samples["order_date"],
            "reference_id":
                return_samples["order_id"],
        }
    )

    # -----------------------------------------
    # Generate damages
    # -----------------------------------------

    damage_records = []

    for i in range(1, 2001):

        product_id = random.choice(
            products["product_id"].tolist()
        )

        warehouse_id = random.choice(
            warehouse_ids
        )

        quantity = random.randint(
            1,
            20,
        )

        transaction_date = pd.Timestamp(
            start_date
            + pd.Timedelta(
                days=random.randint(
                    0,
                    (end_date - start_date).days,
                )
            )
        )

        damage_records.append(
            {
                "transaction_id":
                    f"TXN-DAMAGE-{i:08d}",

                "product_id":
                    product_id,

                "warehouse_id":
                    warehouse_id,

                "transaction_type":
                    "DAMAGE",

                "quantity":
                    quantity,

                "transaction_date":
                    transaction_date,

                "reference_id":
                    None,
            }
        )

    damage_transactions = pd.DataFrame(
        damage_records
    )

    # -----------------------------------------
    # Combine everything
    # -----------------------------------------

    transactions = pd.concat(
        [
            sales_transactions,
            purchase_transactions,
            return_transactions,
            damage_transactions,
        ],
        ignore_index=True,
    )

    transactions[
        "transaction_date"
    ] = pd.to_datetime(
        transactions[
            "transaction_date"
        ]
    )

    transactions = transactions.sort_values(
        "transaction_date"
    ).reset_index(drop=True)

    # -----------------------------------------
    # Save
    # -----------------------------------------

    output = (
        SYNTHETIC_DIR
        / "inventory_transactions.csv"
    )

    transactions.to_csv(
        output,
        index=False,
    )

    print(
        f"\nGenerated "
        f"{len(transactions):,} "
        f"inventory transactions"
    )

    print(
        f"Saved → {output}"
    )

    print("\nTransaction distribution:")

    print(
        transactions[
            "transaction_type"
        ].value_counts()
    )

    return transactions


if __name__ == "__main__":
    generate_inventory_transactions()
