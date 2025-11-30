"""
Prescriptions Router - API endpoints for managing prescription uploads
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from services.ocr_service import ocr_service
from services.storage_service import storage_service

router = APIRouter(
    prefix="/api/prescriptions",
    tags=["Prescriptions"]
)


@router.post("/upload")
async def upload_prescription(file: UploadFile = File(...)):
    """
    Upload a prescription image:
    1. Extract patient name using OCR
    2. Upload to Cloud Storage
    3. Return details

    - **file**: Image file (JPG, PNG, etc.)
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}"
        )

    # Read file content
    try:
        contents = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Could not read file: {str(e)}"
        )

    # Check file size (max 10MB)
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 10MB"
        )

    # Step 1: Extract patient name using OCR
    try:
        ocr_result = ocr_service.extract_patient_name(contents)
        patient_name = ocr_result.get("patient_name")

        if not patient_name:
            raise HTTPException(
                status_code=400,
                detail="Could not extract patient name from prescription"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"OCR failed: {str(e)}"
        )

    # Step 2: Upload to Cloud Storage
    try:
        # Get file extension
        file_ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"

        storage_result = storage_service.upload_prescription(
            image_content=contents,
            patient_name=patient_name,
            file_extension=file_ext
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Storage upload failed: {str(e)}"
        )

    # Return complete result
    return {
        "success": True,
        "message": "Prescription uploaded successfully",
        "ocr": ocr_result,
        "storage": storage_result
    }


@router.get("/patients")
async def list_patients():
    """
    Get list of all patients (sorted alphabetically by name).
    """
    try:
        patients = storage_service.list_all_patients()
        return {
            "success": True,
            "count": len(patients),
            "patients": patients
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list patients: {str(e)}"
        )


@router.get("/patients/{patient_name}")
async def get_patient_prescriptions(patient_name: str):
    """
    Get all prescriptions for a specific patient.

    - **patient_name**: Patient name (e.g., "john_doe")
    """
    try:
        prescriptions = storage_service.list_prescriptions_by_patient(patient_name)

        # Generate signed URLs for each prescription
        results = []
        for blob_name in prescriptions:
            url = storage_service.get_signed_url(blob_name)
            results.append({
                "blob_name": blob_name,
                "url": url
            })

        return {
            "success": True,
            "patient_name": patient_name,
            "count": len(results),
            "prescriptions": results
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get prescriptions: {str(e)}"
        )