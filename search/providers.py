"""Provider registry for marketplace search modules."""

from search.amazon import fetch_amazon_products
from search.blinkit import fetch_blinkit_products
from search.flipkart import fetch_flipkart_products
from search.instamart import fetch_instamart_products


PROVIDERS = {
    "instamart": fetch_instamart_products,
    "amazon": fetch_amazon_products,
    "flipkart": fetch_flipkart_products,
    "blinkit": fetch_blinkit_products,
}


def fetch_provider_products(provider, query, limit=6):
    """Fetch products from a single registered provider."""
    if provider not in PROVIDERS:
        raise ValueError(f"Unknown provider: {provider}")

    return PROVIDERS[provider](query=query, limit=limit)


def fetch_all_providers(query, limit=6):
    """Fetch all registered providers and preserve per-provider failures."""
    results = {}

    for name, fetch_products in PROVIDERS.items():
        try:
            results[name] = fetch_products(query=query, limit=limit)
        except Exception as error:
            results[name] = {
                "provider": name,
                "query": query,
                "count": 0,
                "products": [],
                "status": "error",
                "error": str(error),
            }

    return results
