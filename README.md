# Instamart Image Search

FastAPI app that lets a user upload a product image, classifies the visible grocery product with Gemini, and returns the top Instamart matches.

## Run

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_key_here
```

Install dependencies from `pyproject.toml`, then run:

```powershell
fastapi dev
```

FastAPI discovers `main.py`, which exposes:

```python
from frontend.app import app
```

Open:

```text
http://127.0.0.1:8000/
```

## Structure

```text
main.py                  FastAPI discovery entrypoint
frontend/app.py          API routes, Gemini image classification, static file serving
frontend/templates/      Browser UI HTML
frontend/static/         Browser UI CSS and JavaScript
search/instamart.py      Raw HTTP Instamart search client and response normalization
```

## API

`POST /api/search-image`

Multipart form field:

```text
image=<uploaded image file>
```

Response:

```json
{
  "detected_product": "Diet Coke",
  "products": [
    {
      "product_name": "Coca-Cola Diet Coke Can",
      "price": {"amount": 50, "currency": "INR"},
      "qty": "330 ml",
      "weight": 330,
      "rating": {"value": "4.5", "count": "6.1k"},
      "link": "https://instamart.in/item/ESO83PE1OK",
      "image_url": "https://media-assets.swiggy.com/..."
    }
  ]
}
```

## Notes

- The Gemini API key stays server-side; the browser never receives it.
- Instamart is queried server-side with raw HTTP because its search API is not a browser-facing public API.
- Proxy environment variables are cleared in the backend and Instamart client to avoid stale local proxy failures on Windows.
