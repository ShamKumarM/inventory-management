from pathlib import Path
import pandas as pd


class InventoryCopilot:
    """
    Business intelligence layer on top of the Cookd AI Decision Engine.

    Reads:
        data/processed/ai_decisions.csv

    Provides:
        - risk summaries
        - priority actions
        - expiry analysis
        - promotion opportunities
        - replenishment opportunities
        - product explanations
        - natural-language-ready responses
    """

    def __init__(self, decisions_path=None):

        if decisions_path is None:
            decisions_path = (
                Path(__file__).resolve().parents[2]
                / "data"
                / "processed"
                / "ai_decisions.csv"
            )

        self.decisions_path = Path(decisions_path)

        if not self.decisions_path.exists():
            raise FileNotFoundError(
                f"AI decisions file not found: {self.decisions_path}\n"
                "Run the AI Decision Engine first."
            )

        self.df = pd.read_csv(self.decisions_path)

        if self.df.empty:
            raise ValueError("AI decisions dataset is empty.")

        self._prepare_data()

        print(f"Copilot loaded: {len(self.df)} products")

    # ---------------------------------------------------------
    # DATA PREPARATION
    # ---------------------------------------------------------

    def _prepare_data(self):

        numeric_columns = [
            "overall_risk_score",
            "recommended_quantity",
            "expiry_quantity",
            "days_to_expiry",
            "forecast_7d",
            "current_stock",
            "reorder_point",
            "days_of_inventory",
        ]

        for column in numeric_columns:

            if column in self.df.columns:
                self.df[column] = pd.to_numeric(
                    self.df[column],
                    errors="coerce"
                ).fillna(0)

    # ---------------------------------------------------------
    # OVERVIEW
    # ---------------------------------------------------------

    def get_overview(self):

        total_products = len(self.df)

        critical = self._count(
            "overall_risk_level",
            "CRITICAL"
        )

        high = self._count(
            "overall_risk_level",
            "HIGH"
        )

        medium = self._count(
            "overall_risk_level",
            "MEDIUM"
        )

        low = self._count(
            "overall_risk_level",
            "LOW"
        )

        expiry_quantity = self.df.get(
            "expiry_quantity",
            pd.Series([0])
        ).sum()

        return {
            "total_products": total_products,
            "critical_risks": critical,
            "high_risks": high,
            "medium_risks": medium,
            "low_risks": low,
            "total_expiring_units": float(expiry_quantity),
        }

    # ---------------------------------------------------------
    # RISK SUMMARY
    # ---------------------------------------------------------

    def get_risk_summary(self):

        if "overall_risk_level" not in self.df.columns:
            return {}

        return (
            self.df["overall_risk_level"]
            .value_counts()
            .to_dict()
        )

    # ---------------------------------------------------------
    # PRIMARY RISKS
    # ---------------------------------------------------------

    def get_primary_risks(self):

        if "primary_risk" not in self.df.columns:
            return {}

        return (
            self.df["primary_risk"]
            .value_counts()
            .to_dict()
        )

    # ---------------------------------------------------------
    # PRIORITY ACTIONS
    # ---------------------------------------------------------

    def get_priority_actions(self, limit=10):

        columns = [
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

        available = [
            column
            for column in columns
            if column in self.df.columns
        ]

        result = self.df[available].copy()

        if "overall_risk_score" in result.columns:
            result = result.sort_values(
                "overall_risk_score",
                ascending=False
            )

        return result.head(limit)

    # ---------------------------------------------------------
    # EXPIRY RISKS
    # ---------------------------------------------------------

    def get_expiry_risks(self, limit=10):

        if "expiry_quantity" not in self.df.columns:
            return pd.DataFrame()

        result = self.df[
            self.df["expiry_quantity"] > 0
        ].copy()

        if "days_to_expiry" in result.columns:
            result = result.sort_values(
                ["days_to_expiry", "expiry_quantity"],
                ascending=[True, False]
            )

        columns = [
            "product_id",
            "product_name",
            "expiry_quantity",
            "days_to_expiry",
            "recommended_action",
            "overall_risk_score",
        ]

        available = [
            column
            for column in columns
            if column in result.columns
        ]

        return result[available].head(limit)

    # ---------------------------------------------------------
    # PROMOTION OPPORTUNITIES
    # ---------------------------------------------------------

    def get_promotion_opportunities(self, limit=10):

        if "recommended_action" not in self.df.columns:
            return pd.DataFrame()

        promotion_actions = [
            "PROMOTION / BUNDLE",
            "IMMEDIATE CLEARANCE",
        ]

        result = self.df[
            self.df["recommended_action"].isin(
                promotion_actions
            )
        ].copy()

        if "expiry_quantity" in result.columns:
            result = result.sort_values(
                "expiry_quantity",
                ascending=False
            )

        columns = [
            "product_id",
            "product_name",
            "recommended_action",
            "expiry_quantity",
            "days_to_expiry",
            "overall_risk_score",
        ]

        available = [
            column
            for column in columns
            if column in result.columns
        ]

        return result[available].head(limit)

    # ---------------------------------------------------------
    # REORDER OPPORTUNITIES
    # ---------------------------------------------------------

    def get_reorder_opportunities(self, limit=10):

        if "recommended_quantity" not in self.df.columns:
            return pd.DataFrame()

        result = self.df[
            self.df["recommended_quantity"] > 0
        ].copy()

        result = result.sort_values(
            "recommended_quantity",
            ascending=False
        )

        columns = [
            "product_id",
            "product_name",
            "forecast_7d",
            "current_stock",
            "reorder_point",
            "recommended_quantity",
            "overall_risk_level",
            "recommended_action",
        ]

        available = [
            column
            for column in columns
            if column in result.columns
        ]

        return result[available].head(limit)

    # ---------------------------------------------------------
    # PRODUCT LOOKUP
    # ---------------------------------------------------------

    def get_product(self, product_id):

        result = self.df[
            self.df["product_id"].astype(str).str.upper()
            == str(product_id).upper()
        ]

        if result.empty:
            return None

        return result.iloc[0].to_dict()

    # ---------------------------------------------------------
    # PRODUCT EXPLANATION
    # ---------------------------------------------------------

    def explain_product(self, product_id):

        product = self.get_product(product_id)

        if product is None:
            return f"I couldn't find product {product_id}."

        product_name = product.get(
            "product_name",
            product_id
        )

        risk = product.get(
            "overall_risk_level",
            "UNKNOWN"
        )

        score = product.get(
            "overall_risk_score",
            0
        )

        primary_risk = product.get(
            "primary_risk",
            "UNKNOWN"
        )

        action = product.get(
            "recommended_action",
            "NO ACTION"
        )

        forecast = product.get(
            "forecast_7d",
            0
        )

        current_stock = product.get(
            "current_stock",
            0
        )

        expiry_quantity = product.get(
            "expiry_quantity",
            0
        )

        days_to_expiry = product.get(
            "days_to_expiry",
            0
        )

        return (
            f"{product_name} ({product_id})\n\n"
            f"Risk: {risk}\n"
            f"Risk Score: {score:.2f}\n"
            f"Primary Risk: {primary_risk}\n\n"
            f"Current Stock: {current_stock:,.2f} units\n"
            f"7-Day Forecast: {forecast:,.2f} units\n"
            f"Expiring Quantity: {expiry_quantity:,.2f} units\n"
            f"Days to Expiry: {days_to_expiry:.0f}\n\n"
            f"Recommended Action: {action}"
        )

    # ---------------------------------------------------------
    # NATURAL LANGUAGE QUERY
    # ---------------------------------------------------------

    def ask(self, question):

        q = question.lower().strip()

        # Product-specific question
        for product_id in self.df["product_id"].astype(str):

            if product_id.lower() in q:

                return self.explain_product(product_id)

        # Expiry
        if any(
            word in q
            for word in [
                "expiry",
                "expire",
                "expiring",
            ]
        ):

            result = self.get_expiry_risks(10)

            if result.empty:
                return "There are no expiry risks currently."

            return self._format_dataframe(
                "Products approaching expiry",
                result
            )

        # Promotion
        if any(
            word in q
            for word in [
                "promote",
                "promotion",
                "bundle",
                "clearance",
                "overstock",
            ]
        ):

            result = self.get_promotion_opportunities(10)

            if result.empty:
                return "There are no promotion opportunities."

            return self._format_dataframe(
                "Promotion opportunities",
                result
            )

        # Reorder
        if any(
            word in q
            for word in [
                "reorder",
                "replenish",
                "purchase",
                "buy",
            ]
        ):

            result = self.get_reorder_opportunities(10)

            if result.empty:
                return "There are currently no products requiring reorder."

            return self._format_dataframe(
                "Reorder opportunities",
                result
            )

        # Risk
        if any(
            word in q
            for word in [
                "risk",
                "danger",
                "critical",
            ]
        ):

            result = self.get_priority_actions(10)

            return self._format_dataframe(
                "Highest-risk products",
                result
            )

        # Overview
        if any(
            word in q
            for word in [
                "overview",
                "summary",
                "status",
                "inventory",
            ]
        ):

            return self._format_overview()

        return (
            "I can help with:\n\n"
            "• Inventory overview\n"
            "• Expiry risks\n"
            "• Promotion opportunities\n"
            "• Reorder recommendations\n"
            "• Product risk analysis\n"
            "• Product-specific explanations"
        )

    # ---------------------------------------------------------
    # FORMATTING
    # ---------------------------------------------------------

    def _format_overview(self):

        overview = self.get_overview()

        return (
            "COOKD INVENTORY AI — OVERVIEW\n\n"
            f"Products: {overview['total_products']:,}\n"
            f"Critical Risks: {overview['critical_risks']:,}\n"
            f"High Risks: {overview['high_risks']:,}\n"
            f"Medium Risks: {overview['medium_risks']:,}\n"
            f"Low Risks: {overview['low_risks']:,}\n"
            f"Expiring Units: "
            f"{overview['total_expiring_units']:,.0f}"
        )

    def _format_dataframe(self, title, df):

        if df.empty:
            return f"{title}\n\nNo results found."

        lines = [
            title,
            "-" * len(title),
        ]

        for _, row in df.iterrows():

            product_id = row.get(
                "product_id",
                ""
            )

            product_name = row.get(
                "product_name",
                ""
            )

            action = row.get(
                "recommended_action",
                ""
            )

            expiry = row.get(
                "expiry_quantity",
                None
            )

            days = row.get(
                "days_to_expiry",
                None
            )

            line = f"{product_id} — {product_name}"

            if action:
                line += f" | {action}"

            if expiry is not None:
                line += f" | Expiring: {expiry:,.0f}"

            if days is not None:
                line += f" | {days:.0f} days"

            lines.append(line)

        return "\n".join(lines)

    # ---------------------------------------------------------
    # HELPERS
    # ---------------------------------------------------------

    def _count(self, column, value):

        if column not in self.df.columns:
            return 0

        return int(
            (
                self.df[column]
                .astype(str)
                .str.upper()
                == value.upper()
            ).sum()
        )


# =============================================================
# CLI TEST
# =============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("COOKD INVENTORY AI COPILOT")
    print("=" * 70)

    copilot = InventoryCopilot()

    print("\nOVERVIEW")
    print("-" * 50)
    print(copilot._format_overview())

    print("\n\nPRODUCT EXPLANATION")
    print("-" * 50)
    print(
        copilot.explain_product("PRD0044")
    )

    print("\n\nCOPILOT QUERY")
    print("-" * 50)
    print(
        copilot.ask(
            "Which products should I promote?"
        )
    )