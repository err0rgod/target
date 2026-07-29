const form = document.querySelector("#uploadForm");
const imageInput = document.querySelector("#imageInput");
const dropZone = document.querySelector("#dropZone");
const dropTitle = document.querySelector("#dropTitle");
const dropMeta = document.querySelector("#dropMeta");
const previewRow = document.querySelector("#previewRow");
const previewImage = document.querySelector("#previewImage");
const fileName = document.querySelector("#fileName");
const clearButton = document.querySelector("#clearButton");
const submitButton = document.querySelector("#submitButton");
const statusPill = document.querySelector("#statusPill");
const resultTitle = document.querySelector("#resultTitle");
const resultCount = document.querySelector("#resultCount");
const emptyState = document.querySelector("#emptyState");
const productsGrid = document.querySelector("#productsGrid");
const productTemplate = document.querySelector("#productTemplate");
const emptyStateText = emptyState.querySelector("p");

let selectedFile = null;
let previewUrl = null;

function setStatus(text, mode = "") {
  statusPill.textContent = text;
  statusPill.className = `status-pill ${mode}`.trim();
}

function formatPrice(price) {
  if (!price || price.amount === undefined || price.amount === null) {
    return "Price unavailable";
  }
  return `${price.currency || "INR"} ${price.amount}`;
}

function formatRating(rating) {
  if (!rating || !rating.value) {
    return "No rating";
  }
  return rating.count ? `${rating.value} (${rating.count})` : rating.value;
}

function formatWeight(weight) {
  if (weight === undefined || weight === null || weight === "") {
    return "Weight unavailable";
  }
  return `${weight} g`;
}

function resetPreview() {
  selectedFile = null;
  imageInput.value = "";
  previewRow.hidden = true;
  previewImage.removeAttribute("src");
  dropTitle.textContent = "Choose image";
  dropMeta.textContent = "PNG, JPG, WEBP up to 8 MB";

  if (previewUrl) {
    URL.revokeObjectURL(previewUrl);
    previewUrl = null;
  }
}

function resetResults(message = "Results will appear here after the image is processed.") {
  productsGrid.innerHTML = "";
  emptyState.hidden = false;
  emptyStateText.textContent = message;
  resultTitle.textContent = "No search yet";
  resultCount.textContent = "0 items";
}

function useFile(file) {
  if (!file) {
    return;
  }

  if (!file.type.startsWith("image/")) {
    setStatus("Image only", "error");
    return;
  }

  selectedFile = file;
  if (previewUrl) {
    URL.revokeObjectURL(previewUrl);
  }

  previewUrl = URL.createObjectURL(file);
  previewImage.src = previewUrl;
  fileName.textContent = file.name;
  previewRow.hidden = false;
  dropTitle.textContent = "Image selected";
  dropMeta.textContent = `${Math.round(file.size / 1024)} KB`;
  setStatus("Ready");
}

function renderProducts(products) {
  productsGrid.innerHTML = "";
  emptyState.hidden = products.length > 0;
  resultCount.textContent = `${products.length} item${products.length === 1 ? "" : "s"}`;

  products.forEach((product) => {
    const node = productTemplate.content.cloneNode(true);
    const card = node.querySelector(".product-card");
    const imageLink = node.querySelector(".product-image-link");
    const image = node.querySelector(".product-image");
    const name = node.querySelector(".product-name");
    const price = node.querySelector(".price");
    const rating = node.querySelector(".rating");
    const qty = node.querySelector(".qty");
    const weight = node.querySelector(".weight");

    const link = product.link || "#";
    const productName = product.product_name || "Unnamed product";

    imageLink.href = link;
    image.alt = productName;

    if (product.image_url) {
      image.src = product.image_url;
      image.onerror = () => {
        image.remove();
        card.classList.add("missing-image");
      };
    } else {
      image.remove();
      card.classList.add("missing-image");
    }

    name.href = link;
    name.textContent = productName;
    price.textContent = formatPrice(product.price);
    rating.textContent = formatRating(product.rating);
    qty.textContent = product.qty || "Qty unavailable";
    weight.textContent = formatWeight(product.weight);

    productsGrid.appendChild(node);
  });
}

async function submitImage(event) {
  event.preventDefault();

  if (!selectedFile) {
    setStatus("Choose image", "error");
    return;
  }

  const body = new FormData();
  body.append("image", selectedFile);

  setStatus("Searching", "loading");
  submitButton.disabled = true;
  resultTitle.textContent = "Processing image";
  resultCount.textContent = "0 items";
  emptyState.hidden = false;
  emptyStateText.textContent = "Classifying image and searching Instamart.";
  productsGrid.innerHTML = "";

  try {
    const response = await fetch("/api/search-image", {
      method: "POST",
      body,
    });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || data.error || "Search failed.");
    }

    resultTitle.textContent = data.detected_product
      ? `Detected: ${data.detected_product}`
      : "Detected product";
    renderProducts(data.products || []);
    setStatus("Done");
  } catch (error) {
    resultTitle.textContent = "Search failed";
    resultCount.textContent = "0 items";
    emptyState.hidden = false;
    emptyStateText.textContent = error.message;
    setStatus("Error", "error");
  } finally {
    submitButton.disabled = false;
  }
}

imageInput.addEventListener("change", () => useFile(imageInput.files[0]));
clearButton.addEventListener("click", resetPreview);
form.addEventListener("submit", submitImage);
window.addEventListener("pageshow", () => {
  if (!selectedFile) {
    resetPreview();
    resetResults();
  }
});

dropZone.addEventListener("dragover", (event) => {
  event.preventDefault();
  dropZone.classList.add("dragging");
});

dropZone.addEventListener("dragleave", () => {
  dropZone.classList.remove("dragging");
});

dropZone.addEventListener("drop", (event) => {
  event.preventDefault();
  dropZone.classList.remove("dragging");
  useFile(event.dataTransfer.files[0]);
});
