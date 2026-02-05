FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for OCR libraries (includes tesseract-ocr)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    gcc \
    g++ \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (full OCR/ML stack)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download model weights during build (avoids HuggingFace rate limits at runtime)
RUN python -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='juliozhao/DocLayout-YOLO-DocStructBench', filename='doclayout_yolo_docstructbench_imgsz1024.pt')"

# Pre-download TrOCR handwritten model (small enough to include in image)
RUN python -c "from transformers import TrOCRProcessor, VisionEncoderDecoderModel; TrOCRProcessor.from_pretrained('microsoft/trocr-base-handwritten'); VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-base-handwritten')"

# Copy application code
COPY . .

# Cloud Run uses PORT env var (defaults to 8080)
EXPOSE 8080

# Run with uvicorn on the PORT provided by Cloud Run
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
