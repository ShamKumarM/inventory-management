import pandas as pd

from src.config import (
    SYNTHETIC_DIR,
    START_DATE,
    END_DATE,
)


def generate_inventory_snapshots():

    print("Loading datasets...")

    products = pd.read_csv(
        SYNTHETIC_DIR / "products.csv"
    )

    warehouses = pd.read_csv(
        SYNTHETIC_DIR / "warehouses.csv"
    )

    transactions = pd.read_csv(
        SYNTHETIC_DIR
        / "inventory_transactions.csv"
    )

    transactions["transaction_date"] = pd.to_datetime(
        transactions["transaction_date"]
    )

    # -----------------------------------------
    # Create complete date range
    # -----------------------------------------

    dates = pd.date_range(
        START_DATE,
        END_DATE,
        freq="D",
    )

    # -----------------------------------------
    # Create product × warehouse combinations
    # -----------------------------------------

    product_ids = products[
        "product_id"
    ].tolist()

    warehouse_ids = warehouses[
        "warehouse_id"
    ].tolist()

    combinations = pd.MultiIndex.from_product(
        [
            dates,
            product_ids,
            warehouse_ids,
        ],
        names=[
            "date",
            "product_id",
            "warehouse_id",
        ],
    )

    snapshots = pd.DataFrame(
        index=combinations
    ).reset_index()

    # -----------------------------------------
    # Aggregate transactions by date/product/
    # warehouse/type
    # -----------------------------------------

    transaction_pivot = (
        transactions
        .pivot_table(
            index=[
                "transaction_date",
                "product_id",
                "warehouse_id",
            ],
            columns="transaction_type",
            values="quantity",
            aggfunc="sum",
            fill_value=0,
        )
        .reset_index()
    )

    transaction_pivot = (
        transaction_pivot
        .rename(
            columns={
                "transaction_date": "date",
                "PURCHASE": "received_quantity",
                "SALE": "sold_quantity",
                "RETURN": "returned_quantity",
                "DAMAGE": "damaged_quantity",
            }
        )
    )

    # Make sure missing transaction columns exist

    for column in [
        "received_quantity",
        "sold_quantity",
        "returned_quantity",
        "damaged_quantity",
    ]:

        if column not in transaction_pivot.columns:

            transaction_pivot[column] = 0

    # -----------------------------------------
    # Merge transactions into daily grid
    # -----------------------------------------

    snapshots = snapshots.merge(
        transaction_pivot[
            [
                "date",
                "product_id",
                "warehouse_id",
                "received_quantity",
                "sold_quantity",
                "returned_quantity",
                "damaged_quantity",
            ]
        ],
        on=[
            "date",
            "product_id",
            "warehouse_id",
        ],
        how="left",
    )

    snapshots = snapshots.fillna(0)

    # -----------------------------------------
    # Calculate stock
    # -----------------------------------------

    snapshots = snapshots.sort_values(
        [
            "product_id",
            "warehouse_id",
            "date",
        ]
    )

    snapshots["net_change"] = (
        snapshots["received_quantity"]
        + snapshots["returned_quantity"]
        - snapshots["sold_quantity"]
        - snapshots["damaged_quantity"]
    )

    snapshots["closing_stock"] = (
        snapshots
        .groupby(
            [
                "product_id",
                "warehouse_id",
            ]
        )["net_change"]
        .cumsum()
    )

    # -----------------------------------------
    # Opening stock
    # -----------------------------------------

    snapshots["opening_stock"] = (
        snapshots
        .groupby(
            [
                "product_id",
                "warehouse_id",
            ]
        )["closing_stock"]
        .shift(1)
        .fillna(0)
    )

    # -----------------------------------------
    # Prevent negative stock
    # -----------------------------------------

    snapshots["closing_stock"] = (
        snapshots["closing_stock"]
        .clip(lower=0)
    )

    # -----------------------------------------
    # Stock status
    # -----------------------------------------

    snapshots["stock_status"] = "normal"

    snapshots.loc[
        snapshots["closing_stock"] <= 0,
        "stock_status",
    ] = "out_of_stock"

    # -----------------------------------------
    # Save
    # -----------------------------------------

    output = (
        SYNTHETIC_DIR
        / "inventory_snapshots.csv"
    )

    snapshots.to_csv(
        output,
        index=False,
    )

    print(
        f"\nGenerated "
        f"{len(snapshots):,} "
        f"inventory snapshots"
    )

    print(
        f"Saved → {output}"
    )

    print("\nStock status:")

    print(
        snapshots[
            "stock_status"
        ].value_counts()
    )

    print("\nFinal stock:")

    print(
        snapshots[
            "closing_stock"
        ].describe()
    )

    return snapshots


if __name__ == "__main__":
    generate_inventory_snapshots()