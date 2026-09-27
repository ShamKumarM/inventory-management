from pathlib import Path
import sys

import pandas as pd
import streamlit as st


# ============================================================
# PATHS
# ============================================================

ROOT_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = ROOT_DIR / "data" / "synthetic"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"

AI_DECISIONS = PROCESSED_DIR / "ai_decisions.csv"
PRODUCTS = DATA_DIR / "products.csv"
INVENTORY = DATA_DIR / "inventory_snapshots.csv"


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Cookd Inventory AI",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main {
        background-color: #f7f8fa;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    .metric-card {
        background: white;
        padding: 18px;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }

    .section-title {
        font-size: 1.35rem;
        font-weight: 700;
        margin-top: 1rem;
        margin-bottom: 0.75rem;
    }

    .risk-critical {
        color: #dc2626;
        font-weight: 700;
    }

    .risk-high {
        color: #ea580c;
        font-weight: 700;
    }

    .risk-medium {
        color: #ca8a04;
        font-weight: 700;
    }

    .risk-low {
        color: #16a34a;
        font-weight: 700;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_decisions():

    if not AI_DECISIONS.exists():
        return pd.DataFrame()

    df = pd.read_csv(AI_DECISIONS)

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

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            ).fillna(0)

    return df


@st.cache_data
def load_products():

    if not PRODUCTS.exists():
        return pd.DataFrame()

    return pd.read_csv(PRODUCTS)


@st.cache_data
def load_inventory():

    if not INVENTORY.exists():
        return pd.DataFrame()

    df = pd.read_csv(INVENTORY)

    if "date" in df.columns:
        df["date"] = pd.to_datetime(
            df["date"],
            errors="coerce"
        )

    return df


decisions = load_decisions()
products = load_products()
inventory = load_inventory()


# ============================================================
# VALIDATION
# ============================================================

if decisions.empty:

    st.error(
        """
        AI decision data not found.

        Run:

        `python -m src.inventory.ai_decision_engine`
        """
    )

    st.stop()


# ============================================================
# IMPORT COPILOT
# ============================================================

sys.path.insert(0, str(ROOT_DIR))

from src.copilot.inventory_copilot import InventoryCopilot


copilot = InventoryCopilot(
    decisions_path=AI_DECISIONS
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("📦 Cookd Inventory AI")

st.sidebar.caption(
    "AI-powered inventory intelligence platform"
)

st.sidebar.divider()

page = st.sidebar.radio(
    "Navigation",
    [
        "📊 Executive Overview",
        "📦 Inventory Intelligence",
        "📈 Demand Forecast",
        "⚠️ Risk & Expiry Center",
        "🤖 AI Copilot",
    ],
)

st.sidebar.divider()

st.sidebar.caption(
    f"Products loaded: {len(decisions):,}"
)

if not inventory.empty:

    latest_date = inventory["date"].max()

    st.sidebar.caption(
        f"Data date: {latest_date.date()}"
    )


# ============================================================
# HEADER
# ============================================================

st.title("Cookd Inventory AI")

st.caption(
    "AI-powered demand forecasting, inventory risk detection "
    "and business recommendations"
)


# ============================================================
# EXECUTIVE OVERVIEW
# ============================================================

if page == "📊 Executive Overview":

    st.markdown(
        '<div class="section-title">Executive Overview</div>',
        unsafe_allow_html=True,
    )

    total_products = len(decisions)

    critical = int(
        (
            decisions["overall_risk_level"]
            == "CRITICAL"
        ).sum()
    )

    high = int(
        (
            decisions["overall_risk_level"]
            == "HIGH"
        ).sum()
    )

    expiring_units = decisions[
        "expiry_quantity"
    ].sum()

    clearance = int(
        (
            decisions["recommended_action"]
            == "IMMEDIATE CLEARANCE"
        ).sum()
    )

    promotion = int(
        (
            decisions["recommended_action"]
            == "PROMOTION / BUNDLE"
        ).sum()
    )

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric(
        "Products",
        f"{total_products:,}"
    )

    col2.metric(
        "Critical Risks",
        f"{critical:,}"
    )

    col3.metric(
        "High Risks",
        f"{high:,}"
    )

    col4.metric(
        "Expiring Units",
        f"{expiring_units:,.0f}"
    )

    col5.metric(
        "Clearance Actions",
        f"{clearance:,}"
    )

    st.divider()

    # --------------------------------------------------------
    # ACTION DISTRIBUTION
    # --------------------------------------------------------

    left, right = st.columns(2)

    with left:

        st.subheader("AI Action Distribution")

        action_counts = (
            decisions["recommended_action"]
            .value_counts()
        )

        st.bar_chart(action_counts)

    with right:

        st.subheader("Primary Risk Distribution")

        risk_counts = (
            decisions["primary_risk"]
            .value_counts()
        )

        st.bar_chart(risk_counts)

    st.divider()

    # --------------------------------------------------------
    # TOP PRIORITIES
    # --------------------------------------------------------

    st.subheader("🔥 Top AI Priorities")

    priority = copilot.get_priority_actions(15)

    st.dataframe(
        priority,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# INVENTORY INTELLIGENCE
# ============================================================

elif page == "📦 Inventory Intelligence":

    st.header("📦 Inventory Intelligence")

    col1, col2, col3 = st.columns(3)

    current_stock = decisions[
        "current_stock"
    ].sum()

    avg_days = decisions[
        "days_of_inventory"
    ].mean()

    reorder_count = int(
        (
            decisions["recommended_quantity"]
            > 0
        ).sum()
    )

    col1.metric(
        "Current Inventory",
        f"{current_stock:,.0f}"
    )

    col2.metric(
        "Avg Days of Inventory",
        f"{avg_days:,.0f}"
    )

    col3.metric(
        "Products Requiring Reorder",
        f"{reorder_count:,}"
    )

    st.divider()

    st.subheader("Inventory Status")

    status_filter = st.multiselect(
        "Risk Level",
        options=sorted(
            decisions["overall_risk_level"]
            .dropna()
            .unique()
        ),
        default=sorted(
            decisions["overall_risk_level"]
            .dropna()
            .unique()
        ),
    )

    filtered = decisions[
        decisions["overall_risk_level"].isin(
            status_filter
        )
    ]

    columns = [
        "product_id",
        "product_name",
        "current_stock",
        "forecast_7d",
        "reorder_point",
        "days_of_inventory",
        "recommended_quantity",
        "overall_risk_level",
    ]

    available = [
        c for c in columns
        if c in filtered.columns
    ]

    st.dataframe(
        filtered[available],
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# DEMAND FORECAST
# ============================================================

elif page == "📈 Demand Forecast":

    st.header("📈 Demand Forecast")

    st.caption(
        "7-day demand predictions generated by the ML demand forecasting model."
    )

    forecast = decisions[
        [
            "product_id",
            "product_name",
            "forecast_7d",
            "current_stock",
            "days_of_inventory",
        ]
    ].copy()

    forecast = forecast.sort_values(
        "forecast_7d",
        ascending=False
    )

    st.subheader("Top Demand Products")

    st.dataframe(
        forecast.head(20),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    selected_product = st.selectbox(
        "Select Product",
        decisions["product_id"].tolist(),
    )

    selected = decisions[
        decisions["product_id"]
        == selected_product
    ]

    if not selected.empty:

        row = selected.iloc[0]

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "7-Day Forecast",
            f"{row['forecast_7d']:.2f}"
        )

        c2.metric(
            "Current Stock",
            f"{row['current_stock']:,.0f}"
        )

        c3.metric(
            "Days of Inventory",
            f"{row['days_of_inventory']:,.0f}"
        )

        st.info(
            copilot.explain_product(
                selected_product
            )
        )


# ============================================================
# RISK & EXPIRY CENTER
# ============================================================

elif page == "⚠️ Risk & Expiry Center":

    st.header("⚠️ Risk & Expiry Center")

    critical = decisions[
        decisions["overall_risk_level"]
        == "CRITICAL"
    ]

    st.metric(
        "Critical Products",
        len(critical)
    )

    st.divider()

    st.subheader("🚨 Products Approaching Expiry")

    expiry = copilot.get_expiry_risks(25)

    st.dataframe(
        expiry,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.subheader("🔥 Promotion / Clearance Opportunities")

    promotions = copilot.get_promotion_opportunities(
        25
    )

    st.dataframe(
        promotions,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# AI COPILOT
# ============================================================

elif page == "🤖 AI Copilot":

    st.header("🤖 Inventory AI Copilot")

    st.caption(
        "Ask questions about Cookd inventory, demand, risk and actions."
    )

    question = st.text_input(
        "Ask your inventory question",
        placeholder=(
            "Which products should I promote?"
        ),
    )

    examples = [
        "Which products should I promote?",
        "Which products are expiring?",
        "Which products need reorder?",
        "Show me the highest risk products",
        "Give me inventory overview",
        "Why is PRD0044 risky?",
    ]

    st.write("Try:")

    cols = st.columns(3)

    for index, example in enumerate(examples):

        with cols[index % 3]:

            if st.button(
                example,
                key=f"example_{index}",
                use_container_width=True,
            ):

                question = example

    if question:

        st.divider()

        st.subheader("AI Response")

        response = copilot.ask(question)

        st.code(
            response,
            language="text"
        )

    else:

        st.info(
            "Ask me about inventory, expiry, "
            "reorder, promotions or product risks."
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Cookd Inventory AI • Demand Forecasting • "
    "Risk Intelligence • AI Recommendations"
)