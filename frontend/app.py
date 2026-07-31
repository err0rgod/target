"""FastAPI backend for image-based Instamart product search."""

import mimetypes
import os
import sys
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from google import genai
from google.genai import types


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from search.providers import fetch_all_providers


MODEL_NAME = "gemini-3.6-flash"
PROMPT = (
    "Classify this image. Return only the simple grocery product name visible in the image. "
    "Do not include explanation, punctuation, brand guesses unless the brand is clearly visible, "
    "or extra words."
)
MAX_IMAGE_BYTES = 8 * 1024 * 1024
PROXY_ENV_KEYS = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
)


app = FastAPI(title="Instamart Image Search")
app.mount("/static", StaticFiles(directory=FRONTEND_ROOT / "static"), name="static")


@app.middleware("http")
async def no_cache_assets(request, call_next):
    """Disable frontend caching during local development."""
    response = await call_next(request)
    if request.url.path == "/" or request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-store, max-age=0"
        response.headers["Pragma"] = "no-cache"
    return response


def load_dotenv(dotenv_path):
    """Load simple KEY=VALUE pairs from .env without adding a dependency."""
    if not dotenv_path.exists():
        return

    for line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key and key not in os.environ:
            os.environ[key] = value


def clear_proxy_environment():
    """Avoid stale localhost proxy settings breaking outbound API calls."""
    for key in PROXY_ENV_KEYS:
        os.environ.pop(key, None)

    os.environ["NO_PROXY"] = "127.0.0.1,localhost,instamart.in,*.instamart.in,googleapis.com,*.googleapis.com"
    os.environ["no_proxy"] = os.environ["NO_PROXY"]


def classify_image_bytes(image_bytes, mime_type):
    """Return Gemini's concise product-name classification for uploaded bytes."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY was not found. Add it to .env or your environment.")

    clear_proxy_environment()
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[
            PROMPT,
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
        ],
    )

    return (response.text or "").strip()


@app.on_event("startup")
def startup():
    """Initialize environment configuration when FastAPI starts."""
    load_dotenv(PROJECT_ROOT / ".env")
    clear_proxy_environment()


@app.get("/")
def index():
    """Serve the single-page upload UI."""
    return FileResponse(FRONTEND_ROOT / "templates" / "index.html")


@app.post("/api/search-image")
async def search_image(image: UploadFile = File(...)):
    """Classify an uploaded image and return the top five Instamart matches."""
    mime_type = image.content_type or mimetypes.guess_type(image.filename or "")[0]
    if not mime_type or not mime_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="The uploaded file must be an image.")

    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="The uploaded image is empty.")
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=400, detail="The uploaded image must be 8 MB or smaller.")

    try:
        detected_product = classify_image_bytes(image_bytes, mime_type)
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Gemini classification failed: {error}") from error

    try:
        provider_results = fetch_all_providers(query=detected_product, limit=6)
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Provider search failed: {error}") from error

    instamart_results = provider_results.get("instamart", {})

    return {
        "detected_product": detected_product,
        "products": instamart_results.get("products", []),
        "providers": provider_results,
    }
