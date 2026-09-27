from pathlib import Path

# Project root
BASE_DIR = Path(__file__).resolve().parent.parent

# Data directories
DATA_DIR = BASE_DIR / "data"
SYNTHETIC_DIR = DATA_DIR / "synthetic"

SYNTHETIC_DIR.mkdir(parents=True, exist_ok=True)

# Reproducibility
RANDOM_SEED = 42

# Dataset sizes
NUM_SUPPLIERS = 15
NUM_PRODUCTS = 100
NUM_CUSTOMERS = 5_000

NUM_ORDERS = 20_000

# Historical period
START_DATE = "2024-01-01"
END_DATE = "2026-09-30"

# Indian business configuration
CITIES = [
    "Chennai",
    "Bengaluru",
    "Hyderabad",
    "Mumbai",
    "Pune",
    "Delhi",
    "Kochi",
    "Coimbatore",
    "Madurai",
    "Trichy",
]

STATES = {
    "Chennai": "Tamil Nadu",
    "Coimbatore": "Tamil Nadu",
    "Madurai": "Tamil Nadu",
    "Trichy": "Tamil Nadu",
    "Bengaluru": "Karnataka",
    "Hyderabad": "Telangana",
    "Mumbai": "Maharashtra",
    "Pune": "Maharashtra",
    "Delhi": "Delhi",
    "Kochi": "Kerala",
}

# Product categories
PRODUCT_CATEGORIES = {
    "Masala": [
        "Biriyani Masala",
        "Chicken 65 Masala",
        "Sambar Masala",
        "Rasam Masala",
        "Garam Masala",
        "Curry Masala",
    ],
    "Podis": [
        "Idli Podi",
        "Curry Leaf Podi",
        "Garlic Podi",
        "Paruppu Podi",
    ],
    "Instant Mix": [
        "Dosa Mix",
        "Idli Mix",
        "Adai Mix",
        "Paniyaram Mix",
    ],
    "Cooking Paste": [
        "Ginger Garlic Paste",
        "Tandoori Paste",
        "Chettinad Paste",
    ],
    "Snacks": [
        "Murukku",
        "Mixture",
        "Banana Chips",
        "Nendran Chips",
    ],
}

# Product pack sizes
PACK_SIZES = [
    100,
    200,
    250,
    500,
    1000,
]

# Product price ranges
PRICE_RANGES = {
    "Masala": (80, 220),
    "Podis": (90, 250),
    "Instant Mix": (100, 280),
    "Cooking Paste": (120, 300),
    "Snacks": (70, 250),
}

# Supplier lead times
SUPPLIER_LEAD_TIME_RANGE = (2, 14)

# Shelf life
SHELF_LIFE_RANGE = (90, 365)

# Customer configuration

CUSTOMER_SEGMENTS = {
    "new": 0.30,
    "regular": 0.40,
    "loyal": 0.20,
    "high_value": 0.10,
}

ORDER_CHANNELS = {
    "website": 0.55,
    "marketplace": 0.25,
    "whatsapp": 0.10,
    "instagram": 0.05,
    "other": 0.05,
}

ORDER_STATUSES = {
    "delivered": 0.90,
    "cancelled": 0.04,
    "returned": 0.03,
    "processing": 0.02,
    "shipped": 0.01,
}