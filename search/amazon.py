"""Amazon India search provider stub.

This module intentionally returns search links only. Amazon frequently blocks or
reshapes raw HTML responses, so product extraction should be added here once you
choose the scraping/API strategy you want to maintain.
"""

from urllib.parse import urlencode


BASE_URL = "https://www.amazon.in"
SEARCH_PATH = "/s"
LIMIT = 5


def search_url(query):
    params = urlencode({"k": query or ""})
    return f"{BASE_URL}{SEARCH_PATH}?{params}"


def fetch_amazon_products(query, limit=LIMIT):
    """Return Amazon provider metadata in the shared provider shape."""
    return {
        "provider": "amazon",
        "query": query,
        "count": 0,
        "search_url": search_url(query),
        "products": [],
        "status": "not_implemented",
    }
