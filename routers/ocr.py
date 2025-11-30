"""
OCR Router - API endpoints for text extraction from prescription images
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from services.ocr_service import ocr_service

router = APIRouter(
    prefix="/api/ocr",
    tags=["OCR"]
)


@router.post("/extract-name")
async def extract_patient_name(file: UploadFile = File(...)):
    """
    Extract patient name from a prescription image.

    - **file**: Image file (JPG, PNG, etc.)

    Returns the extracted patient name along with confidence level.
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Allowed: {allowed_types}"
        )

    # Read file content
    try:
        contents = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read file: {str(e)}")

    # Check file size (max 10MB)
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB")

    # Extract patient name using OCR
    try:
        result = ocr_service.extract_patient_name(contents)
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")


@router.post("/extract-text")
async def extract_all_text(file: UploadFile = File(...)):
    """
    Extract all text from an image (useful for debugging).

    - **file**: Image file (JPG, PNG, etc.)

    Returns all detected text from the image.
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Allowed: {allowed_types}"
        )

    # Read file content
    try:
        contents = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read file: {str(e)}")

    # Extract text using OCR
    try:
        text = ocr_service.extract_text_from_image(contents)
        return {
            "success": True,
            "text": text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")
