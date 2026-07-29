import mimetypes
import os
from pathlib import Path

from google import genai
from google.genai import types


MODEL_NAME = "gemini-3.6-flash"
IMAGE_PATH = r"D:\target\images\image.png"
PROMPT = (
    "Classify this image. Return a concise answer with the primary category, "
    "important visible objects, and a short confidence note."
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


def classify_image() -> str:
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
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[
            PROMPT,
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
        ],
    )

    return response.text or ""


def main() -> None:
    load_dotenv(Path(".env"))
    result = classify_image()
    print(result)


if __name__ == "__main__":
    main()
