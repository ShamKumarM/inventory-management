import pandas as pd

from src.config import SYNTHETIC_DIR


def run_eda():

    print("=" * 70)
    print("COOKD INVENTORY — EDA REPORT")
    print("=" * 70)

    products = pd.read_csv(
        SYNTHETIC_DIR / "products.csv"
    )

    orders = pd.read_csv(
        SYNTHETIC_DIR / "orders.csv"
    )

    order_items = pd.read_csv(
        SYNTHETIC_DIR / "order_items.csv"
    )

    snapshots = pd.read_csv(
        SYNTHETIC_DIR / "inventory_snapshots.csv"
    )

    transactions = pd.read_csv(
        SYNTHETIC_DIR / "inventory_transactions.csv"
    )

    orders["order_date"] = pd.to_datetime(
        orders["order_date"]
    )

    snapshots["date"] = pd.to_datetime(
        snapshots["date"]
    )

    transactions["transaction_date"] = pd.to_datetime(
        transactions["transaction_date"]
    )

    # =====================================================
    # 1. SALES OVERVIEW
    # =====================================================

    print("\n1. SALES OVERVIEW")
    print("-" * 50)

    total_units = order_items["quantity"].sum()

    total_revenue = order_items[
        "line_total"
    ].sum()

    total_orders = orders["order_id"].nunique()

    avg_order_value = (
        total_revenue / total_orders
    )

    print(f"Orders:          {total_orders:,}")
    print(f"Units sold:      {total_units:,}")
    print(f"Revenue:         ₹{total_revenue:,.2f}")
    print(f"Average order:   ₹{avg_order_value:,.2f}")

    # =====================================================
    # 2. TOP PRODUCTS
    # =====================================================

    print("\n2. TOP PRODUCTS BY UNITS")
    print("-" * 50)

    product_sales = (
        order_items
        .groupby("product_id")
        .agg(
            units_sold=("quantity", "sum"),
            revenue=("line_total", "sum"),
            orders=("order_id", "nunique"),
        )
        .sort_values(
            "units_sold",
            ascending=False,
        )
    )

    top_products = product_sales.head(10)

    print(top_products)

    # =====================================================
    # 3. CATEGORY PERFORMANCE
    # =====================================================

    print("\n3. CATEGORY PERFORMANCE")
    print("-" * 50)

    category_sales = (
        order_items
        .merge(
            products[
                [
                    "product_id",
                    "category",
                ]
            ],
            on="product_id",
            how="left",
        )
        .groupby("category")
        .agg(
            units_sold=("quantity", "sum"),
            revenue=("line_total", "sum"),
        )
        .sort_values(
            "revenue",
            ascending=False,
        )
    )

    print(category_sales)

    # =====================================================
    # 4. CHANNEL PERFORMANCE
    # =====================================================

    print("\n4. SALES BY CHANNEL")
    print("-" * 50)

    channel_sales = (
        orders
        .groupby("channel")
        .agg(
            orders=("order_id", "count"),
        )
        .sort_values(
            "orders",
            ascending=False,
        )
    )

    print(channel_sales)

    # =====================================================
    # 5. MONTHLY DEMAND
    # =====================================================

    print("\n5. MONTHLY DEMAND")
    print("-" * 50)

    monthly = (
        order_items
        .merge(
            orders[
                [
                    "order_id",
                    "order_date",
                ]
            ],
            on="order_id",
            how="left",
        )
    )

    monthly["month"] = (
        monthly["order_date"]
        .dt.to_period("M")
    )

    monthly_demand = (
        monthly
        .groupby("month")
        .agg(
            units_sold=("quantity", "sum"),
            revenue=("line_total", "sum"),
            orders=("order_id", "nunique"),
        )
    )

    print(
        monthly_demand.tail(12)
    )

    # =====================================================
    # 6. INVENTORY OVERVIEW
    # =====================================================

    print("\n6. INVENTORY OVERVIEW")
    print("-" * 50)

    latest_date = snapshots["date"].max()

    latest_inventory = snapshots[
        snapshots["date"] == latest_date
    ]

    print(
        f"Snapshot date: {latest_date.date()}"
    )

    print(
        f"Total inventory units: "
        f"{latest_inventory['closing_stock'].sum():,.0f}"
    )

    out_of_stock_count = (
        latest_inventory["closing_stock"] <= 0
    ).sum()

    print(
        f"Out-of-stock observations: "
        f"{out_of_stock_count:,}"
    )

    # =====================================================
    # 7. PRODUCT DEMAND METRICS
    # =====================================================

    print("\n7. PRODUCT DEMAND METRICS")
    print("-" * 50)

    daily_demand = (
        transactions[
            transactions["transaction_type"]
            == "SALE"
        ]
        .groupby(
            [
                "transaction_date",
                "product_id",
            ]
        )["quantity"]
        .sum()
        .reset_index()
    )

    demand_metrics = (
        daily_demand
        .groupby("product_id")
        .agg(
            avg_daily_demand=(
                "quantity",
                "mean",
            ),
            demand_std=(
                "quantity",
                "std",
            ),
            max_daily_demand=(
                "quantity",
                "max",
            ),
            active_days=(
                "transaction_date",
                "nunique",
            ),
        )
    )

    demand_metrics[
        "demand_std"
    ] = demand_metrics[
        "demand_std"
    ].fillna(0)

    demand_metrics[
        "coefficient_of_variation"
    ] = (
        demand_metrics["demand_std"]
        / demand_metrics[
            "avg_daily_demand"
        ].replace(0, pd.NA)
    )

    print(
        demand_metrics
        .sort_values(
            "avg_daily_demand",
            ascending=False,
        )
        .head(10)
    )

    # =====================================================
    # 8. STOCKOUT ANALYSIS
    # =====================================================

    print("\n8. STOCKOUT ANALYSIS")
    print("-" * 50)

    stockout_summary = (
        snapshots
        .groupby("product_id")
        .agg(
            stockout_days=(
                "stock_status",
                lambda x: (
                    x == "out_of_stock"
                ).sum(),
            ),
            avg_stock=(
                "closing_stock",
                "mean",
            ),
            min_stock=(
                "closing_stock",
                "min",
            ),
        )
        .sort_values(
            "stockout_days",
            ascending=False,
        )
    )

    print(
        stockout_summary.head(10)
    )

    # =====================================================
    # 9. DAYS OF INVENTORY
    # =====================================================

    latest_stock = (
        latest_inventory
        .groupby("product_id")
        ["closing_stock"]
        .sum()
    )

    avg_demand = (
        demand_metrics[
            "avg_daily_demand"
        ]
    )

    inventory_health = pd.DataFrame(
        {
            "current_stock":
                latest_stock,

            "avg_daily_demand":
                avg_demand,
        }
    )

    inventory_health[
        "days_of_inventory"
    ] = (
        inventory_health[
            "current_stock"
        ]
        / inventory_health[
            "avg_daily_demand"
        ].replace(0, pd.NA)
    )

    print("\n9. LOWEST DAYS OF INVENTORY")
    print("-" * 50)

    print(
        inventory_health
        .sort_values(
            "days_of_inventory"
        )
        .head(10)
    )

    # =====================================================
    # 10. SAVE REPORT DATA
    # =====================================================

    report_dir = (
        SYNTHETIC_DIR.parent.parent
        / "reports"
    )

    report_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    product_sales.to_csv(
        report_dir
        / "product_sales.csv"
    )

    category_sales.to_csv(
        report_dir
        / "category_sales.csv"
    )

    demand_metrics.to_csv(
        report_dir
        / "demand_metrics.csv"
    )

    stockout_summary.to_csv(
        report_dir
        / "stockout_summary.csv"
    )

    inventory_health.to_csv(
        report_dir
        / "inventory_health.csv"
    )

    print("\n" + "=" * 70)
    print("EDA COMPLETE")
    print(
        f"Reports saved → {report_dir}"
    )
    print("=" * 70)


if __name__ == "__main__":
    run_eda()