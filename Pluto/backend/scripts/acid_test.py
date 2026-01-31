
"""
Acid Test: Multimodal RAG Alignment (Fully Automated)
1. Generates a sample image and text file if not present
2. Uploads both to the /ingest endpoint
3. Queries Qdrant for semantic similarity
4. Prints a clear success rate
"""
import requests
import time
import os
from PIL import Image, ImageDraw, ImageFont

image_found = False
text_found = False

API_URL = "http://localhost:8000/api/v1/ingest/file"
QUERY_URL = "http://localhost:8000/api/v1/query/"
ASSET_DIR = os.path.abspath("test_assets")
os.makedirs(ASSET_DIR, exist_ok=True)
IMAGE_PATH = os.path.join(ASSET_DIR, "red_circuit_board.jpg")
TEXT_PATH = os.path.join(ASSET_DIR, "ruby_substrate.txt")

# Generate a simple red circuit board image if not present
if not os.path.exists(IMAGE_PATH):
    img = Image.new("RGB", (256, 256), color=(180, 0, 0))  # type: ignore
    draw = ImageDraw.Draw(img)
    # Draw some "circuit" lines
    for i in range(20, 236, 40):
        draw.line((i, 20, i, 236), fill=(255, 200, 0), width=4)
        draw.line((20, i, 236, i), fill=(255, 200, 0), width=4)
    draw.text((30, 120), "CIRCUIT", fill=(255,255,255))
    img.save(IMAGE_PATH, "JPEG")
    print(f"Generated sample image at {IMAGE_PATH}")

# Generate a sample text file if not present
if not os.path.exists(TEXT_PATH):
    with open(TEXT_PATH, "w", encoding="utf-8") as f:
        f.write("The hardware utilizes a ruby-colored substrate for the wiring.")
    print(f"Generated sample text at {TEXT_PATH}")

# Step A: Upload image
with open(IMAGE_PATH, "rb") as img_file:
    files = {"file": (os.path.basename(IMAGE_PATH), img_file, "image/jpeg")}
    resp_img = requests.post(API_URL, files=files)
    print("Image upload status:", resp_img.status_code, resp_img.text)

# Step B: Upload text file
with open(TEXT_PATH, "rb") as txt_file:
    files = {"file": (os.path.basename(TEXT_PATH), txt_file, "text/plain")}
    resp_txt = requests.post(API_URL, files=files)
    print("Text upload status:", resp_txt.status_code, resp_txt.text)

# Wait for ingestion to complete
print("Waiting for ingestion...")
time.sleep(5)

success_count = int(image_found) + int(text_found)
success_count = int(image_found) + int(text_found)
# Step C: Query Qdrant
query = {"query": "crimson electronics", "top_k": 3, "collection": "pluto_main"}
resp_query = requests.post(QUERY_URL, json=query)
print("Query status:", resp_query.status_code)
results = resp_query.json()

# --- TRUTH CHECK: Print the full Qdrant results for inspection ---
import json as _json
print("\n--- FULL QDRANT RAW RESULTS ---")
print(_json.dumps(results, indent=2))
print("--- END RAW RESULTS ---\n")

SIMILARITY_THRESHOLD = 0.4
hits = results.get("results", [])
print("Top 3 results:")
image_found = False
text_found = False
for hit in hits:
    print(f"ID: {hit.get('id')}, Score: {hit.get('score')}, Modality: {hit.get('metadata', {}).get('modality')}")
    if 'metadata' in hit and 'file_name' in hit['metadata']:
        print(f"DEBUG: Found {hit['metadata']['file_name']} with score {hit['score']}")
    if hit.get('metadata', {}).get('modality', '').startswith('image') and hit.get('score', 0) > SIMILARITY_THRESHOLD:
        image_found = True
    if hit.get('metadata', {}).get('modality', '') == 'text' and hit.get('score', 0) > SIMILARITY_THRESHOLD:
        text_found = True

success_count = int(image_found) + int(text_found)
print(f"\nSuccess Rate: {success_count}/2 modalities matched with high similarity (>{SIMILARITY_THRESHOLD})")
if image_found and text_found:
    print("ACID TEST PASSED: Both image and text file are highly similar to the query.")
else:
    print("ACID TEST FAILED: One or both modalities missing or below similarity threshold.")
