import pandas as pd

from src.config import SYNTHETIC_DIR


def load(name):
    path = SYNTHETIC_DIR / name
    return pd.read_csv(path)


def check_duplicates(df, column):
    count = df[column].duplicated().sum()

    print(
        f"{column}: "
        f"{count:,} duplicate values"
    )

    return count


def check_missing(df):

    missing = df.isnull().sum()

    missing = missing[
        missing > 0
    ]

    if len(missing) == 0:
        print("Missing values: NONE")
    else:
        print("Missing values:")
        print(missing)


def validate():

    print("=" * 60)
    print("COOKD INVENTORY DATA QUALITY CHECK")
    print("=" * 60)

    products = load("products.csv")
    suppliers = load("suppliers.csv")
    customers = load("customers.csv")
    orders = load("orders.csv")
    order_items = load("order_items.csv")
    warehouses = load("warehouses.csv")
    transactions = load(
        "inventory_transactions.csv"
    )
    batches = load(
        "inventory_batches.csv"
    )
    snapshots = load(
        "inventory_snapshots.csv"
    )

    # -----------------------------------------
    # Dataset sizes
    # -----------------------------------------

    print("\nDATASET SIZES")
    print("-" * 40)

    datasets = {
        "suppliers": suppliers,
        "products": products,
        "customers": customers,
        "orders": orders,
        "order_items": order_items,
        "warehouses": warehouses,
        "transactions": transactions,
        "batches": batches,
        "snapshots": snapshots,
    }

    for name, df in datasets.items():

        print(
            f"{name:<20}"
            f"{len(df):>10,}"
        )

    # -----------------------------------------
    # Duplicate checks
    # -----------------------------------------

    print("\nDUPLICATE CHECKS")
    print("-" * 40)

    check_duplicates(
        products,
        "product_id",
    )

    check_duplicates(
        suppliers,
        "supplier_id",
    )

    check_duplicates(
        customers,
        "customer_id",
    )

    check_duplicates(
        orders,
        "order_id",
    )

    check_duplicates(
        order_items,
        "order_item_id",
    )

    check_duplicates(
        warehouses,
        "warehouse_id",
    )

    check_duplicates(
        transactions,
        "transaction_id",
    )

    check_duplicates(
        batches,
        "batch_id",
    )

    # -----------------------------------------
    # Missing values
    # -----------------------------------------

    print("\nMISSING VALUES")
    print("-" * 40)

    for name, df in datasets.items():

        print(f"\n{name}")

        check_missing(df)

    # -----------------------------------------
    # Foreign keys
    # -----------------------------------------

    print("\nFOREIGN KEY CHECKS")
    print("-" * 40)

    valid_products = set(
        products["product_id"]
    )

    valid_customers = set(
        customers["customer_id"]
    )

    valid_orders = set(
        orders["order_id"]
    )

    valid_warehouses = set(
        warehouses["warehouse_id"]
    )

    invalid_order_customers = (
        orders[
            ~orders["customer_id"].isin(
                valid_customers
            )
        ]
    )

    invalid_item_orders = (
        order_items[
            ~order_items["order_id"].isin(
                valid_orders
            )
        ]
    )

    invalid_item_products = (
        order_items[
            ~order_items["product_id"].isin(
                valid_products
            )
        ]
    )

    invalid_transaction_products = (
        transactions[
            ~transactions["product_id"].isin(
                valid_products
            )
        ]
    )

    invalid_transaction_warehouses = (
        transactions[
            ~transactions["warehouse_id"].isin(
                valid_warehouses
            )
        ]
    )

    print(
        "Invalid order customers:",
        len(invalid_order_customers),
    )

    print(
        "Invalid order references:",
        len(invalid_item_orders),
    )

    print(
        "Invalid item products:",
        len(invalid_item_products),
    )

    print(
        "Invalid transaction products:",
        len(invalid_transaction_products),
    )

    print(
        "Invalid transaction warehouses:",
        len(invalid_transaction_warehouses),
    )

    # -----------------------------------------
    # Quantity checks
    # -----------------------------------------

    print("\nQUANTITY CHECKS")
    print("-" * 40)

    print(
        "Negative order quantities:",
        (
            order_items["quantity"] < 0
        ).sum(),
    )

    print(
        "Zero order quantities:",
        (
            order_items["quantity"] == 0
        ).sum(),
    )

    print(
        "Negative transaction quantities:",
        (
            transactions["quantity"] < 0
        ).sum(),
    )

    # -----------------------------------------
    # Price checks
    # -----------------------------------------

    print("\nPRICE CHECKS")
    print("-" * 40)

    print(
        "Products with invalid selling price:",
        (
            products["selling_price"] <= 0
        ).sum(),
    )

    print(
        "Products with cost >= selling price:",
        (
            products["cost_price"]
            >= products["selling_price"]
        ).sum(),
    )

    # -----------------------------------------
    # Inventory checks
    # -----------------------------------------

    print("\nINVENTORY CHECKS")
    print("-" * 40)

    print(
        "Negative closing stock:",
        (
            snapshots["closing_stock"] < 0
        ).sum(),
    )

    print(
        "Out-of-stock observations:",
        (
            snapshots["stock_status"]
            == "out_of_stock"
        ).sum(),
    )

    # -----------------------------------------
    # Date checks
    # -----------------------------------------

    print("\nDATE CHECKS")
    print("-" * 40)

    orders["order_date"] = pd.to_datetime(
        orders["order_date"]
    )

    transactions[
        "transaction_date"
    ] = pd.to_datetime(
        transactions["transaction_date"]
    )

    batches["expiry_date"] = pd.to_datetime(
        batches["expiry_date"]
    )

    print(
        "Order date:",
        orders["order_date"].min(),
        "→",
        orders["order_date"].max(),
    )

    print(
        "Transaction date:",
        transactions[
            "transaction_date"
        ].min(),
        "→",
        transactions[
            "transaction_date"
        ].max(),
    )

    print(
        "Expiry date:",
        batches["expiry_date"].min(),
        "→",
        batches["expiry_date"].max(),
    )

    print("\n" + "=" * 60)
    print("DATA QUALITY CHECK COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    validate()