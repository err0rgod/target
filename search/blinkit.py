"""Blinkit search provider stub.

Blinkit availability depends heavily on location and browser/session state. This
module gives the app a provider boundary without pretending to have product data.
"""

from urllib.parse import urlencode


BASE_URL = "https://blinkit.com"
SEARCH_PATH = "/s/"
LIMIT = 5


def search_url(query):
    params = urlencode({"q": query or ""})
    return f"{BASE_URL}{SEARCH_PATH}?{params}"


def fetch_blinkit_products(query, limit=LIMIT):
    """Return Blinkit provider metadata in the shared provider shape."""
    return {
        "provider": "blinkit",
        "query": query,
        "count": 0,
        "search_url": search_url(query),
        "products": [],
        "status": "not_implemented",
    }
