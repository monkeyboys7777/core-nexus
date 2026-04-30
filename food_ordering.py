"""
food_ordering.py — Core Nexus Food Ordering
Opens restaurant websites directly and navigates to the ordering/menu page.
Hands off to the user at the customisation/checkout screen.
Requires: pip install selenium webdriver-manager
"""

import os
import time
import webbrowser

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


# ── Restaurant registry ────────────────────────────────────────────────────────
# Each entry:
#   order_url   — direct link to the online ordering / menu page
#   search_url  — fallback: search for location if order_url needs postcode
#   keywords    — spoken name variants
#   navigate_fn — optional function name to call for deeper navigation

RESTAURANTS = {
    "dominos": {
        "keywords": ["dominos", "domino's", "dominoes", "domino"],
        "order_url": "https://www.dominos.com/en/pages/order/",
        "canada_url": "https://www.dominos.ca/en/pages/order/",
        "description": "Domino's Pizza",
        "can_autonavigate": True,
    },
    "kfc": {
        "keywords": ["kfc", "kentucky fried chicken", "kentucky"],
        "order_url": "https://www.kfc.com/menu",
        "description": "KFC",
        "can_autonavigate": False,
    },
    "subway": {
        "keywords": ["subway"],
        "order_url": "https://www.subway.com/en-CA/MenuNutrition/Menu",
        "description": "Subway",
        "can_autonavigate": False,
    },
    "mcdonalds": {
        "keywords": ["mcdonalds", "mcdonald's", "maccas", "mcd", "micky d"],
        "order_url": "https://www.mcdonalds.com/ca/en-ca/order.html",
        "description": "McDonald's",
        "can_autonavigate": False,
    },
    "burger king": {
        "keywords": ["burger king", "bk", "burgerking"],
        "order_url": "https://www.bk.com/menu",
        "description": "Burger King",
        "can_autonavigate": False,
    },
    "pizza hut": {
        "keywords": ["pizza hut", "pizzahut"],
        "order_url": "https://www.pizzahut.ca/menu",
        "description": "Pizza Hut",
        "can_autonavigate": False,
    },
    "wendys": {
        "keywords": ["wendys", "wendy's"],
        "order_url": "https://www.wendys.com/order",
        "description": "Wendy's",
        "can_autonavigate": False,
    },
    "taco bell": {
        "keywords": ["taco bell", "tacobell", "taco"],
        "order_url": "https://www.tacobell.ca/food",
        "description": "Taco Bell",
        "can_autonavigate": False,
    },
    "popeyes": {
        "keywords": ["popeyes", "popeye's"],
        "order_url": "https://www.popeyes.ca/en/order",
        "description": "Popeyes",
        "can_autonavigate": False,
    },
    "a&w": {
        "keywords": ["a&w", "a and w", "aw", "a w"],
        "order_url": "https://www.aw.ca/en/our-food/",
        "description": "A&W",
        "can_autonavigate": False,
    },
    "harveys": {
        "keywords": ["harveys", "harvey's"],
        "order_url": "https://www.harveys.ca/en/menu.html",
        "description": "Harvey's",
        "can_autonavigate": False,
    },
    "swiss chalet": {
        "keywords": ["swiss chalet", "swisschalet"],
        "order_url": "https://www.swisschalet.com/en/order-online",
        "description": "Swiss Chalet",
        "can_autonavigate": False,
    },
    "starbucks": {
        "keywords": ["starbucks", "starbs"],
        "order_url": "https://www.starbucks.ca/menu",
        "description": "Starbucks",
        "can_autonavigate": False,
    },
    "tim hortons": {
        "keywords": ["tim hortons", "tims", "timmy's", "tim's"],
        "order_url": "https://www.timhortons.ca/menu",
        "description": "Tim Hortons",
        "can_autonavigate": False,
    },
    "boston pizza": {
        "keywords": ["boston pizza", "bp", "bostonpizza"],
        "order_url": "https://www.bostonpizza.com/en/order-online",
        "description": "Boston Pizza",
        "can_autonavigate": False,
    },
}

# Menu item keywords → category/URL fragments for Dominos (most structured API)
DOMINOS_ITEMS = {
    "pizza":       "/en/pages/order/#!/category/pizza",
    "pepperoni":   "/en/pages/order/#!/category/pizza",
    "cheese":      "/en/pages/order/#!/category/pizza",
    "chicken":     "/en/pages/order/#!/category/pizza?product=chicken",
    "pasta":       "/en/pages/order/#!/category/pasta",
    "sandwich":    "/en/pages/order/#!/category/sandwiches",
    "wings":       "/en/pages/order/#!/category/chicken",
    "bread":       "/en/pages/order/#!/category/breads",
    "dessert":     "/en/pages/order/#!/category/desserts",
    "drinks":      "/en/pages/order/#!/category/drinks",
    "sides":       "/en/pages/order/#!/category/sides",
}


def match_restaurant(spoken: str) -> tuple[str, dict] | tuple[None, None]:
    """Match a spoken restaurant name to the registry."""
    spoken_lower = spoken.lower().strip()
    for key, info in RESTAURANTS.items():
        if any(kw in spoken_lower or spoken_lower in kw for kw in info["keywords"]):
            return key, info
    return None, None


def _make_driver() -> "webdriver.Chrome":
    """Create a Chrome WebDriver instance."""
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    # Use existing Chrome profile so you're already logged in
    user_data = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
    if os.path.isdir(user_data):
        options.add_argument(f"--user-data-dir={user_data}")
        options.add_argument("--profile-directory=Default")

    service = Service(ChromeDriverManager().install())
    driver  = webdriver.Chrome(service=service, options=options)
    # Mask automation flags
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver


def _navigate_dominos(driver, item: str | None):
    """Navigate Dominos to the right category page."""
    base = "https://www.dominos.ca"
    category_path = "/en/pages/order/"
    if item:
        item_lower = item.lower()
        for keyword, path in DOMINOS_ITEMS.items():
            if keyword in item_lower:
                category_path = path
                break
    driver.get(base + category_path)
    print(f"  [FOOD] Navigated to Dominos: {base + category_path}")


def order_food(restaurant: str, item: str | None = None, use_selenium: bool = True) -> str:
    """
    Open the restaurant ordering page.
    If use_selenium=True and Selenium available, navigate to specific item page.
    Returns status message.
    """
    key, info = match_restaurant(restaurant)

    if not info:
        # Unknown restaurant — fall back to Google search
        query = f"{restaurant} order online"
        url   = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        webbrowser.open(url)
        return f"I don't have a direct link for {restaurant}, Sir. I've searched for their ordering page instead."

    desc = info["description"]

    if use_selenium and SELENIUM_AVAILABLE and info.get("can_autonavigate"):
        try:
            driver = _make_driver()
            if key == "dominos":
                _navigate_dominos(driver, item)
            msg = f"Opened {desc} ordering page, Sir. Navigate to your item and I'll stand by while you complete checkout."
            return msg
        except Exception as e:
            print(f"  [FOOD] Selenium failed ({e}), falling back to browser open")

    # Fallback: just open the URL in default browser
    url = info.get("order_url", "")
    if url:
        webbrowser.open(url)
        item_str = f" for {item}" if item else ""
        return (
            f"Opened {desc} ordering page{item_str}, Sir. "
            f"Select your items and complete checkout when ready."
        )

    return f"Could not find an ordering page for {desc}, Sir."


def find_reservation(restaurant: str) -> str:
    """Open OpenTable or restaurant's own reservation page."""
    key, info = match_restaurant(restaurant)
    desc = info["description"] if info else restaurant

    # Try OpenTable first (most universal)
    query = f"{restaurant} reservation"
    url   = f"https://www.opentable.com/s?term={query.replace(' ', '+')}"
    webbrowser.open(url)
    return f"Opened OpenTable for {desc} reservations, Sir. Select your date and party size to complete the booking."
