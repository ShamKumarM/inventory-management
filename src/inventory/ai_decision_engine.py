"""
COOKD INVENTORY AI
AI Decision Engine

Combines:

Demand Forecast
        ↓
Inventory Engine
        ↓
Risk Engine
        ↓
Recommendation Engine
        ↓
Unified AI Decision

Output:
data/processed/ai_decisions.csv
"""

from pathlib import Path

import pandas as pd

from src.inventory.recommendation_engine import (
    RecommendationEngine
)


class AIDecisionEngine:

    def __init__(self):

        print("Initializing AI Decision Engine...")

        self.recommendation_engine = (
            RecommendationEngine()
        )

        self.risk_engine = (
            self.recommendation_engine
            .risk_engine
        )

        self.inventory_engine = (
            self.risk_engine
            .inventory_engine
        )

        self.products = (
            self.inventory_engine
            .products
        )

        self.output_dir = Path(
            "data/processed"
        )

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

    # =========================================================
    # SINGLE PRODUCT
    # =========================================================

    def decide(self, product_id: str):

        # -----------------------------------------------------
        # Inventory
        # -----------------------------------------------------

        inventory = (
            self.inventory_engine
            .analyze_product(
                product_id
            )
        )

        # -----------------------------------------------------
        # Risk
        # -----------------------------------------------------

        risk = (
            self.risk_engine
            .analyze_product(
                product_id
            )
        )

        # -----------------------------------------------------
        # Recommendation
        # -----------------------------------------------------

        recommendation = (
            self.recommendation_engine
            .recommend(
                product_id
            )
        )

        # -----------------------------------------------------
        # Product information
        # -----------------------------------------------------

        product_rows = self.products[
            self.products["product_id"]
            == product_id
        ]

        if product_rows.empty:

            raise ValueError(
                f"Product not found: {product_id}"
            )

        product = product_rows.iloc[0]

        # -----------------------------------------------------
        # Unified AI Decision
        # -----------------------------------------------------

        decision = {

            # Product
            "product_id":
                product_id,

            "product_name":
                product["product_name"],

            "category":
                product["category"],

            # Inventory
            "current_stock":
                inventory["current_stock"],

            "forecast_7d":
                inventory["forecast_7d"],

            "daily_demand":
                inventory["daily_demand"],

            "days_of_inventory":
                inventory["days_of_inventory"],

            "reorder_point":
                inventory["reorder_point"],

            "minimum_stock":
                inventory["minimum_stock"],

            "maximum_stock":
                inventory["maximum_stock"],

            # Supplier
            "supplier":
                inventory["supplier"],

            "supplier_reliability":
                inventory[
                    "supplier_reliability"
                ],

            "lead_time_days":
                inventory["lead_time_days"],

            # -------------------------------------------------
            # Stockout Risk
            # -------------------------------------------------

            "stockout_score":
                risk["stockout"]["score"],

            "stockout_risk":
                risk["stockout"]["level"],

            # -------------------------------------------------
            # Overstock Risk
            # -------------------------------------------------

            "overstock_score":
                risk["overstock"]["score"],

            "overstock_risk":
                risk["overstock"]["level"],

            # -------------------------------------------------
            # Expiry Risk
            # -------------------------------------------------

            "expiry_score":
                risk["expiry"]["score"],

            "expiry_risk":
                risk["expiry"]["level"],

            "expiry_quantity":
                risk["expiry"][
                    "expiring_quantity"
                ],

            "expiry_quantity_60d":
                risk["expiry"][
                    "expiring_quantity_60d"
                ],

            "expiry_quantity_90d":
                risk["expiry"][
                    "expiring_quantity_90d"
                ],

            "days_to_expiry":
                risk["expiry"][
                    "nearest_expiry_days"
                ],

            # -------------------------------------------------
            # Overall Risk
            # -------------------------------------------------

            "overall_risk_score":
                risk["overall_score"],

            "overall_risk_level":
                risk["overall_level"],

            "primary_risk":
                risk["primary_risk"],

            # -------------------------------------------------
            # AI Recommendation
            # -------------------------------------------------

            "recommended_action":
                recommendation["action"],

            "priority":
                recommendation["priority"],

            "recommended_quantity":
                recommendation[
                    "recommended_quantity"
                ],

            "recommendation":
                recommendation[
                    "recommendation"
                ],
        }

        return decision

    # =========================================================
    # ALL PRODUCTS
    # =========================================================

    def run(self):

        print()
        print("=" * 70)
        print("COOKD AI DECISION ENGINE")
        print("=" * 70)

        product_ids = (
            self.products[
                "product_id"
            ]
            .tolist()
        )

        decisions = []

        for product_id in product_ids:

            try:

                decision = self.decide(
                    product_id
                )

                decisions.append(
                    decision
                )

            except Exception as e:

                print(
                    f"Error processing "
                    f"{product_id}: {e}"
                )

        # -----------------------------------------------------
        # Safety check
        # -----------------------------------------------------

        if not decisions:

            raise RuntimeError(
                "No AI decisions were generated."
            )

        df = pd.DataFrame(
            decisions
        )

        # -----------------------------------------------------
        # Save
        # -----------------------------------------------------

        output_path = (
            self.output_dir
            / "ai_decisions.csv"
        )

        df.to_csv(
            output_path,
            index=False
        )

        # =====================================================
        # REPORT
        # =====================================================

        print()
        print(
            f"Products analyzed: "
            f"{len(df)}"
        )

        # -----------------------------------------------------
        # Action summary
        # -----------------------------------------------------

        print()
        print("ACTION SUMMARY")
        print("-" * 50)

        print(
            df[
                "recommended_action"
            ]
            .value_counts()
            .to_string()
        )

        # -----------------------------------------------------
        # Risk summary
        # -----------------------------------------------------

        print()
        print("RISK SUMMARY")
        print("-" * 50)

        print(
            df[
                "overall_risk_level"
            ]
            .value_counts()
            .to_string()
        )

        # -----------------------------------------------------
        # Primary risk
        # -----------------------------------------------------

        print()
        print("PRIMARY RISK")
        print("-" * 50)

        print(
            df[
                "primary_risk"
            ]
            .value_counts()
            .to_string()
        )

        # -----------------------------------------------------
        # Top AI actions
        # -----------------------------------------------------

        print()
        print("TOP AI ACTIONS")
        print("-" * 100)

        display_columns = [

            "product_id",

            "product_name",

            "overall_risk_score",

            "overall_risk_level",

            "primary_risk",

            "recommended_action",

            "recommended_quantity",

            "expiry_quantity",

            "days_to_expiry",
        ]

        print(
            df[
                display_columns
            ]
            .sort_values(
                "overall_risk_score",
                ascending=False
            )
            .head(15)
            .to_string(
                index=False
            )
        )

        # -----------------------------------------------------
        # Output
        # -----------------------------------------------------

        print()
        print(
            f"Saved → {output_path}"
        )

        print("=" * 70)

        return df


# =============================================================
# RUN
# =============================================================

if __name__ == "__main__":

    engine = AIDecisionEngine()

    df = engine.run()