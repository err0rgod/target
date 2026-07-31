"""Flipkart search provider stub.

This module exposes a stable provider function and search URL builder. Add raw
HTML/API extraction here when you decide how to handle Flipkart's dynamic markup.
"""

from urllib.parse import urlencode


BASE_URL = "https://www.flipkart.com"
SEARCH_PATH = "/search"
LIMIT = 5


def search_url(query):
    params = urlencode({"q": query or ""})
    return f"{BASE_URL}{SEARCH_PATH}?{params}"


def fetch_flipkart_products(query, limit=LIMIT):
    """Return Flipkart provider metadata in the shared provider shape."""
    return {
        "provider": "flipkart",
        "query": query,
        "count": 0,
        "search_url": search_url(query),
        "products": [],
        "status": "not_implemented",
    }
