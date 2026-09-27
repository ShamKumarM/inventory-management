import pandas as pd
import numpy as np

from src.config import SYNTHETIC_DIR


def build_demand_dataset():

    print("Loading data...")

    orders = pd.read_csv(
        SYNTHETIC_DIR / "orders.csv"
    )

    order_items = pd.read_csv(
        SYNTHETIC_DIR / "order_items.csv"
    )

    products = pd.read_csv(
        SYNTHETIC_DIR / "products.csv"
    )

    # -----------------------------------------
    # Dates
    # -----------------------------------------

    orders["order_date"] = pd.to_datetime(
        orders["order_date"]
    )

    # -----------------------------------------
    # Only delivered orders represent demand
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
    # Daily product demand
    # -----------------------------------------

    daily_sales = (
        sales
        .groupby(
            [
                "order_date",
                "product_id",
            ]
        )["quantity"]
        .sum()
        .reset_index()
    )

    daily_sales = daily_sales.rename(
        columns={
            "order_date": "date",
            "quantity": "demand",
        }
    )

    # -----------------------------------------
    # Complete product/date grid
    # -----------------------------------------

    dates = pd.date_range(
        daily_sales["date"].min(),
        daily_sales["date"].max(),
        freq="D",
    )

    product_ids = products[
        "product_id"
    ].unique()

    grid = pd.MultiIndex.from_product(
        [
            dates,
            product_ids,
        ],
        names=[
            "date",
            "product_id",
        ],
    ).to_frame(index=False)

    dataset = grid.merge(
        daily_sales,
        on=[
            "date",
            "product_id",
        ],
        how="left",
    )

    dataset["demand"] = (
        dataset["demand"]
        .fillna(0)
    )

    # -----------------------------------------
    # Product information
    # -----------------------------------------

    product_features = products[
        [
            "product_id",
            "category",
            "selling_price",
            "cost_price",
            "popularity",
            "shelf_life_days",
        ]
    ]

    dataset = dataset.merge(
        product_features,
        on="product_id",
        how="left",
    )

    # -----------------------------------------
    # Calendar features
    # -----------------------------------------

    dataset["day_of_week"] = (
        dataset["date"].dt.dayofweek
    )

    dataset["day_of_month"] = (
        dataset["date"].dt.day
    )

    dataset["month"] = (
        dataset["date"].dt.month
    )

    dataset["week_of_year"] = (
        dataset["date"].dt.isocalendar()
        .week
        .astype(int)
    )

    dataset["quarter"] = (
        dataset["date"].dt.quarter
    )

    dataset["is_weekend"] = (
        dataset["day_of_week"] >= 5
    ).astype(int)

    # -----------------------------------------
    # Sort
    # -----------------------------------------

    dataset = dataset.sort_values(
        [
            "product_id",
            "date",
        ]
    ).reset_index(drop=True)

    # -----------------------------------------
    # Lag features
    # -----------------------------------------

    grouped = dataset.groupby(
        "product_id"
    )["demand"]

    dataset["lag_1"] = (
        grouped.shift(1)
    )

    dataset["lag_7"] = (
        grouped.shift(7)
    )

    dataset["lag_14"] = (
        grouped.shift(14)
    )

    dataset["lag_28"] = (
        grouped.shift(28)
    )

    # -----------------------------------------
    # Rolling demand
    # -----------------------------------------

    dataset["rolling_mean_7"] = (
        grouped
        .shift(1)
        .rolling(7)
        .mean()
        .reset_index(
            level=0,
            drop=True,
        )
    )

    dataset["rolling_mean_14"] = (
        grouped
        .shift(1)
        .rolling(14)
        .mean()
        .reset_index(
            level=0,
            drop=True,
        )
    )

    dataset["rolling_mean_28"] = (
        grouped
        .shift(1)
        .rolling(28)
        .mean()
        .reset_index(
            level=0,
            drop=True,
        )
    )

    # -----------------------------------------
    # Rolling volatility
    # -----------------------------------------

    dataset["rolling_std_7"] = (
        grouped
        .shift(1)
        .rolling(7)
        .std()
        .reset_index(
            level=0,
            drop=True,
        )
    )

    dataset["rolling_std_28"] = (
        grouped
        .shift(1)
        .rolling(28)
        .std()
        .reset_index(
            level=0,
            drop=True,
        )
    )

    # -----------------------------------------
    # Future target
    # -----------------------------------------

    dataset["target_7d"] = (
        grouped
        .shift(-1)
        .rolling(7)
        .sum()
        .reset_index(
            level=0,
            drop=True,
        )
    )

    # -----------------------------------------
    # Remove rows without history/target
    # -----------------------------------------

    dataset = dataset.dropna(
        subset=[
            "lag_1",
            "lag_7",
            "lag_14",
            "lag_28",
            "rolling_mean_7",
            "rolling_mean_14",
            "rolling_mean_28",
            "target_7d",
        ]
    )

    # -----------------------------------------
    # Save
    # -----------------------------------------

    output = (
        SYNTHETIC_DIR
        / "demand_ml_dataset.csv"
    )

    dataset.to_csv(
        output,
        index=False,
    )

    print(
        f"\nGenerated "
        f"{len(dataset):,} ML rows"
    )

    print(
        f"Features: "
        f"{dataset.shape[1]}"
    )

    print(
        f"Saved → {output}"
    )

    print("\nTarget statistics:")

    print(
        dataset["target_7d"].describe()
    )

    return dataset


if __name__ == "__main__":
    build_demand_dataset()