import mimetypes
import json
import os
import sys
from pathlib import Path

from google import genai
from google.genai import types


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

MODEL_NAME = "gemini-3.6-flash"
IMAGE_PATH = r"D:\target\images\image.png"
PROMPT = (
    "Classify this image. Return a simple name of the product available in the image, your response will directly be searched " \
    "so you have to just provide a simple name of the product."
)
PROXY_ENV_KEYS = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
)


def load_dotenv(dotenv_path: Path) -> None:
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


def clear_proxy_environment() -> None:
    for key in PROXY_ENV_KEYS:
        os.environ.pop(key, None)

    os.environ["NO_PROXY"] = "127.0.0.1,localhost,instamart.in,*.instamart.in,googleapis.com,*.googleapis.com"
    os.environ["no_proxy"] = os.environ["NO_PROXY"]


def classify_image() -> dict:
    image_path = Path(IMAGE_PATH)
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY was not found. Add it to .env or your environment.")

    if not image_path.exists() or not image_path.is_file():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    mime_type, _ = mimetypes.guess_type(str(image_path))
    if not mime_type or not mime_type.startswith("image/"):
        raise ValueError(f"Could not infer an image MIME type for: {image_path}")

    image_bytes = image_path.read_bytes()
    clear_proxy_environment()
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[
            PROMPT,
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
        ],
    )

    product_name = (response.text or "").strip()

    from search.instamart import fetch_instamart_products
    return fetch_instamart_products(query=product_name)


def main() -> None:
    load_dotenv(Path(".env"))
    clear_proxy_environment()
    result = classify_image()
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
