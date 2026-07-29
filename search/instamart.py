import json
from http.cookiejar import CookieJar
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener


QUERY = "Milk 1 ltr"
LIMIT = 10

BASE_URL = "https://instamart.in"
SEARCH_PAGE_PATH = "/search"
SEARCH_API_PATH = "/api/instamart/search/v2"

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-US,en;q=0.9",
    "content-type": "application/json",
    "origin": BASE_URL,
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0 Safari/537.36"
    ),
}


def money_value(value):
    if not isinstance(value, dict):
        return None

    units = value.get("units")
    nanos = value.get("nanos") or 0
    currency = value.get("currencyCode") or "INR"

    if units is None:
        return None

    amount = float(units) + (float(nanos) / 1_000_000_000)
    if amount.is_integer():
        amount = int(amount)

    return {"amount": amount, "currency": currency}


def selected_variation(product):
    variations = product.get("variations") or []
    for variation in variations:
        if variation.get("listingVariant"):
            return variation
    return variations[0] if variations else {}


def product_rating(product, variation):
    rating = variation.get("rating") or product.get("rating")
    if not isinstance(rating, dict):
        return None

    value = rating.get("value")
    count = rating.get("count")
    if value is None and count is None:
        return None

    return {"value": value, "count": count}


def product_details(product, variation):
    return {
        "quantity": variation.get("quantityDescription"),
        "secondary_quantity": variation.get("secondaryQuantityDescription"),
        "weight_in_grams": variation.get("weightInGrams"),
        "unit_level_price": (variation.get("price") or {}).get("unitLevelPrice") or None,
        "brand": product.get("brand") or variation.get("brandName"),
        "category": variation.get("category"),
        "sub_category": variation.get("subCategoryType"),
        "short_description": variation.get("shortDescription") or None,
        "in_stock": product.get("inStock"),
    }


def normalize_product(product):
    variation = selected_variation(product)
    price = variation.get("price") or {}

    return {
        "product_name": product.get("displayName") or variation.get("displayName"),
        "price": money_value(price.get("offerPrice")),
        "mrp": money_value(price.get("mrp")),
        "rating": product_rating(product, variation),
        "details": product_details(product, variation),
    }


def walk_json(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_json(child)


def extract_products(payload, limit=LIMIT):
    products = []
    seen = set()

    for node in walk_json(payload):
        items = node.get("items")
        if not isinstance(items, list):
            continue

        for item in items:
            if not isinstance(item, dict) or not isinstance(item.get("variations"), list):
                continue

            variation = selected_variation(item)
            product_key = (
                item.get("productId"),
                variation.get("skuId"),
                item.get("displayName"),
            )
            if product_key in seen:
                continue

            seen.add(product_key)
            products.append(normalize_product(item))

            if len(products) >= limit:
                return products

    return products


def build_client():
    cookie_jar = CookieJar()
    return build_opener(HTTPCookieProcessor(cookie_jar))


def request_json(client, url, payload):
    body = json.dumps(payload).encode("utf-8")
    request = Request(url, data=body, headers=HEADERS, method="POST")

    try:
        with client.open(request, timeout=30) as response:
            response_body = response.read().decode("utf-8")
    except HTTPError as error:
        error_body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Instamart API returned HTTP {error.code}: {error_body}") from error
    except URLError as error:
        raise RuntimeError(f"Could not reach Instamart API: {error}") from error

    return json.loads(response_body)


def seed_session(client, query):
    params = urlencode({"custom_back": "true", "query": query})
    url = f"{BASE_URL}{SEARCH_PAGE_PATH}?{params}"
    request = Request(url, headers={k: v for k, v in HEADERS.items() if k != "content-type"})

    try:
        with client.open(request, timeout=30) as response:
            response.read()
    except HTTPError as error:
        raise RuntimeError(f"Instamart search page returned HTTP {error.code}") from error
    except URLError as error:
        raise RuntimeError(f"Could not seed Instamart session: {error}") from error


def fetch_instamart_products(query=QUERY, limit=LIMIT):
    client = build_client()
    seed_session(client, query)

    params = urlencode({"offset": "0", "ageConsent": "false"})
    api_url = f"{BASE_URL}{SEARCH_API_PATH}?{params}"
    payload = {
        "facets": [],
        "sortAttribute": "",
        "query": query,
        "search_results_offset": "0",
        "page_type": "INSTAMART_SEARCH_PAGE",
        "is_pre_search_tag": False,
    }

    response = request_json(client, api_url, payload)
    products = extract_products(response, limit)

    return {
        "query": query,
        "count": len(products),
        "products": products,
    }


def main():
    result = fetch_instamart_products()
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
