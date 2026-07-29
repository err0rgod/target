import json
import mimetypes
import os
import sys
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from google import genai
from google.genai import types


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from search.instamart import fetch_instamart_products


MODEL_NAME = "gemini-3.6-flash"
PROMPT = (
    "Classify this image. Return only the simple grocery product name visible in the image. "
    "Do not include explanation, punctuation, brand guesses unless the brand is clearly visible, "
    "or extra words."
)
MAX_IMAGE_BYTES = 8 * 1024 * 1024


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_IMAGE_BYTES


def load_dotenv(dotenv_path):
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


def classify_image_bytes(image_bytes, mime_type):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY was not found. Add it to .env or your environment.")

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[
            PROMPT,
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
        ],
    )

    return (response.text or "").strip()


def uploaded_image():
    file = request.files.get("image")
    if not file or not file.filename:
        raise ValueError("Upload an image file.")

    image_bytes = file.read()
    if not image_bytes:
        raise ValueError("The uploaded image is empty.")

    mime_type = file.mimetype or mimetypes.guess_type(file.filename)[0]
    if not mime_type or not mime_type.startswith("image/"):
        raise ValueError("The uploaded file must be an image.")

    return image_bytes, mime_type


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/api/search-image")
def search_image():
    try:
        image_bytes, mime_type = uploaded_image()
        detected_product = classify_image_bytes(image_bytes, mime_type)
        results = fetch_instamart_products(query=detected_product, limit=5)
        return jsonify(
            {
                "detected_product": detected_product,
                "products": results["products"],
            }
        )
    except Exception as error:
        return jsonify({"error": str(error)}), 400


if __name__ == "__main__":
    load_dotenv(PROJECT_ROOT / ".env")
    app.run(host="127.0.0.1", port=5000, debug=True)
