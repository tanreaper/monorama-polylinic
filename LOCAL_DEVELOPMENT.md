# Local Development Guide

This guide will help you run the Monorama Polyclinic app on your local machine without needing GCP credentials.

## Prerequisites

- Python 3.9+ installed
- Git installed
- Code editor (VS Code recommended)

## Quick Start (No GCP Required)

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd monorama_polyclinic

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run in Mock Mode (No GCP credentials needed)

```bash
# Set environment variables for mock mode
export USE_MOCK_OCR=true
export USE_MOCK_STORAGE=true

# Run the application
python main.py
```

The app will start on `http://localhost:8080`

### 3. Access the Application

1. Open your browser and go to: `http://localhost:8080/static/index.html`
2. Login credentials:
   - **Username**: `monoramaclinic_admin`
   - **Password**: `monorama2024`

## Mock Mode Features

When running with `USE_MOCK_OCR=true` and `USE_MOCK_STORAGE=true`:

✅ **Works:**
- User authentication (JWT-based)
- Upload prescriptions (stored in memory)
- View patient list (from mock storage)
- View patient prescriptions
- Manual patient name entry
- All UI features

⚠️ **Limitations:**
- OCR returns mock data: "Mock Patient"
- Images stored in memory (lost when app restarts)
- No actual Cloud Storage uploads
- Signed URLs are mock URLs

## What You Can Work On

In mock mode, you can work on:
- Frontend UI improvements
- New features (patient matching, UI enhancements, etc.)
- Authentication flow changes
- Testing and debugging

## Environment Variables

Create a `.env` file (optional):
```bash
# Mock mode (no GCP)
USE_MOCK_OCR=true
USE_MOCK_STORAGE=true

# Production mode (requires GCP credentials)
# USE_MOCK_OCR=false
# USE_MOCK_STORAGE=false
# GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
# GCP_BUCKET_NAME=monorama-polyclinic-prescriptions
```

## Testing Your Changes

```bash
# Run the app
python main.py

# In another terminal, test the API
curl http://localhost:8080/health
```

## Project Structure

```
monorama_polyclinic/
├── main.py                 # FastAPI entry point
├── requirements.txt        # Python dependencies
├── services/
│   ├── ocr_service.py     # OCR with mock mode
│   ├── storage_service.py # Storage with mock mode
│   └── auth_service.py    # Authentication (works offline)
├── routers/
│   ├── prescriptions.py   # Prescription endpoints
│   ├── ocr.py            # OCR endpoints
│   └── auth.py           # Auth endpoints
└── static/
    ├── index.html        # Frontend UI
    └── app.js           # Frontend logic
```

## Common Issues

### Port Already in Use
```bash
# Kill process on port 8080
lsof -ti:8080 | xargs kill -9

# Or use a different port
# Edit main.py and change port number
```

### Module Import Errors
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Cannot Connect to GCP (Even in Mock Mode)
Make sure you set the environment variables:
```bash
export USE_MOCK_OCR=true
export USE_MOCK_STORAGE=true
```

## Need Help?

- Check the main project documentation
- Ask your mentor
- Review the code comments in each service file

## Production Mode (Requires GCP Access)

To run with real GCP services, you'll need:
1. GCP service account key
2. Set `USE_MOCK_OCR=false` and `USE_MOCK_STORAGE=false`
3. Set `GOOGLE_APPLICATION_CREDENTIALS` path
4. Set `GCP_BUCKET_NAME`

Ask your mentor for production credentials if needed.
