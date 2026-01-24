# Vertex AI Workbench Setup Guide

This guide explains how to set up a Vertex AI Workbench notebook instance to run the OCR testing notebooks with full compatibility.

## Prerequisites

- GCP Project with billing enabled
- Vertex AI API enabled
- Cloud Storage bucket (for storing documents)

## Step 1: Enable Required APIs

In Google Cloud Console, enable these APIs:

```bash
# Or run in Cloud Shell:
gcloud services enable notebooks.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable vision.googleapis.com  # Optional: for Cloud Vision OCR
```

## Step 2: Create a Workbench Instance

### Option A: Via Console (Recommended)

1. Go to [Vertex AI Workbench](https://console.cloud.google.com/vertex-ai/workbench)
2. Click **"Create New"** > **"Instances"**
3. Configure:
   - **Name**: `ocr-testing-workbench`
   - **Region**: Choose one close to you (e.g., `us-central1`)
   - **Machine type**: `n1-standard-4` (4 vCPU, 15 GB RAM) - good for OCR
   - **GPU**: None needed (CPU is fine for testing)
   - **Boot disk**: 100 GB SSD
   - **Framework**: **Python 3.10** or **Python 3 (with Intel MKL)**

4. Under **Advanced Options** > **Environment**:
   - Check "Enable terminal"

5. Click **Create**

### Option B: Via gcloud CLI

```bash
gcloud notebooks instances create ocr-testing-workbench \
    --location=us-central1-a \
    --machine-type=n1-standard-4 \
    --boot-disk-size=100GB \
    --boot-disk-type=PD_SSD \
    --no-public-ip=false \
    --metadata=framework=Python:3.10
```

## Step 3: Access the Notebook

1. Wait for the instance to be created (2-3 minutes)
2. Click **"Open JupyterLab"** in the Workbench console
3. A new browser tab opens with JupyterLab

## Step 4: Clone Your Repository

In JupyterLab, open a Terminal and run:

```bash
# Clone your repo (if using Git)
cd /home/jupyter
git clone https://github.com/YOUR_USERNAME/eCourtDateOCR.git

# Or upload files manually via JupyterLab's file browser
```

## Step 5: Install Dependencies

In the Terminal:

```bash
cd /home/jupyter/eCourtDateOCR

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements-cloud.txt
```

## Step 6: Configure GCP Authentication

The Workbench instance automatically has access to GCP services via the attached service account. No additional setup needed!

To verify:
```python
from google.cloud import storage
client = storage.Client()
print(list(client.list_buckets()))  # Should list your buckets
```

## Step 7: Upload Test Documents

Option 1: Upload via JupyterLab file browser (drag & drop)

Option 2: Copy from Cloud Storage:
```bash
gsutil cp -r gs://YOUR_BUCKET/filled_documents ./filled_documents
```

## Step 8: Run Notebooks

1. Navigate to your notebooks in JupyterLab
2. Open any notebook (e.g., `05_ocr_extraction_paddleocr.ipynb`)
3. Select the kernel: **Python 3** (or your venv)
4. Run cells!

---

## Connecting VS Code to Vertex AI Workbench

You can use VS Code locally and connect to the Workbench instance:

### Method 1: VS Code Remote - SSH

1. Get the SSH command from Workbench console:
   - Click on your instance
   - Click "Connect via SSH" dropdown
   - Select "View gcloud command"

2. Set up SSH config:
   ```bash
   gcloud compute config-ssh
   ```

3. In VS Code:
   - Install "Remote - SSH" extension
   - Press `Ctrl+Shift+P` > "Remote-SSH: Connect to Host"
   - Select your Workbench instance

### Method 2: VS Code Web (in JupyterLab)

1. In JupyterLab Terminal:
   ```bash
   pip install code-server
   code-server --bind-addr 0.0.0.0:8080
   ```
2. Access via the provided URL

---

## Cost Management

### Estimated Costs (n1-standard-4):
- ~$0.19/hour when running
- Storage: ~$0.04/GB/month

### To Save Money:
1. **Stop the instance** when not using it:
   ```bash
   gcloud notebooks instances stop ocr-testing-workbench --location=us-central1-a
   ```

2. **Start when needed**:
   ```bash
   gcloud notebooks instances start ocr-testing-workbench --location=us-central1-a
   ```

3. **Set up idle shutdown** (auto-stop after inactivity):
   - In instance settings, enable "Idle shutdown"
   - Set timeout (e.g., 60 minutes)

---

## Syncing Code Between Local and Cloud

### Option 1: Git (Recommended)

Local (VS Code):
```bash
git add .
git commit -m "Update notebooks"
git push
```

Cloud (Workbench):
```bash
git pull
```

### Option 2: Cloud Storage Sync

Upload from local:
```bash
gsutil rsync -r ./notebooks gs://YOUR_BUCKET/notebooks
```

Download to Workbench:
```bash
gsutil rsync -r gs://YOUR_BUCKET/notebooks ./notebooks
```

### Option 3: Direct File Upload

Use JupyterLab's file browser to drag & drop files.

---

## Troubleshooting

### "Permission denied" errors
- Ensure the Workbench service account has required IAM roles:
  - `roles/storage.objectAdmin`
  - `roles/aiplatform.user`

### Package installation fails
- Try: `pip install --upgrade pip setuptools wheel`
- Use: `pip install --no-cache-dir PACKAGE`

### Out of disk space
- Resize boot disk in Console
- Or clean up: `pip cache purge`

### Kernel keeps dying
- Increase machine type (more RAM)
- Process smaller batches of documents
