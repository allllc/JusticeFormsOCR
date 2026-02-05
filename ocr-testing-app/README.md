# Court Form OCR Testing App

Multi-user web application for testing OCR/layout detection pipelines on court forms.

## Features

- **Manage Forms**: Upload and manage base form templates
- **Generate Synthetic Data**: Create filled forms with synthetic data for testing
- **Run Tests**: Process documents with configurable layout detection and OCR libraries
- **View Results**: Side-by-side comparison of expected vs extracted data
- **Metrics**: Aggregate accuracy metrics and per-field breakdown

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: React + Vite + TailwindCSS
- **Database**: Google Cloud Firestore
- **Storage**: Google Cloud Storage
- **Auth**: JWT-based authentication

## Prerequisites

- Python 3.10+
- Node.js 18+
- Google Cloud Project with Firestore and Cloud Storage enabled
- Service account with appropriate permissions

## Setup

### 1. Clone and Setup

```bash
cd ocr-testing-app
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your GCP credentials
```

### 3. Create First User

```bash
cd backend
python scripts/create_user.py --email admin@example.com
# Note the generated password!
```

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
```

### 5. Run Development Servers

Backend:
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Frontend (separate terminal):
```bash
cd frontend
npm run dev
```

Visit http://localhost:3000 and login with your created user.

## Environment Variables

### Backend (.env)

```env
# GCP
GCP_PROJECT_ID=your-project-id
GCP_STORAGE_BUCKET=your-bucket-name
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Auth
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# App
DEBUG=false
CORS_ORIGINS=["http://localhost:3000"]
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Adding New Layout/OCR Libraries

### Layout Detector

1. Create new file: `backend/app/processing/layout/my_detector.py`
2. Inherit from `LayoutDetectorBase`:

```python
from .base import LayoutDetectorBase, Region

class MyDetector(LayoutDetectorBase):
    @property
    def name(self) -> str:
        return "my_detector"

    def detect(self, image: Image.Image) -> List[Region]:
        # Your implementation
        pass
```

3. Register in `backend/app/processing/layout/__init__.py`

### OCR Engine

1. Create new file: `backend/app/processing/ocr/my_ocr.py`
2. Inherit from `OCREngineBase`:

```python
from .base import OCREngineBase, OCRResult

class MyOCREngine(OCREngineBase):
    @property
    def name(self) -> str:
        return "my_ocr"

    def extract_text(self, image: Image.Image, regions: List[Region]) -> List[OCRResult]:
        # Your implementation
        pass
```

3. Register in `backend/app/processing/ocr/__init__.py`

## Project Structure

```
ocr-testing-app/
├── backend/
│   ├── app/
│   │   ├── auth/           # Authentication
│   │   ├── models/         # Pydantic models
│   │   ├── routers/        # API routes
│   │   ├── services/       # Business logic
│   │   └── processing/     # OCR/Layout processors
│   │       ├── layout/     # Layout detectors
│   │       └── ocr/        # OCR engines
│   ├── scripts/            # CLI tools
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API client
│   │   └── context/        # React context
│   └── package.json
└── README.md
```

## License

MIT
