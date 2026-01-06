"""
OCR Service - Extract text from prescription images using Google Cloud Vision API
"""

from google.cloud import vision
import re
from typing import Optional
import io
import os


class OCRService:
    def __init__(self):
        """Initialize the Vision API client"""
        self.use_mock = os.getenv("USE_MOCK_OCR", "false").lower() == "true"
        if not self.use_mock:
            self.client = vision.ImageAnnotatorClient()
        else:
            self.client = None

    def extract_text_from_image(self, image_content: bytes) -> str:
        """
        Extract all text from an image using Google Cloud Vision API.

        Args:
            image_content: Raw bytes of the image

        Returns:
            Extracted text as a string
        """
        # Mock mode for local development without GCP
        if self.use_mock:
            return "Patient Name: Mock Patient\nDate: 2024-01-01\nAge: 30\nSex: M\nWeight: 70kg"

        # Create image object for Vision API
        image = vision.Image(content=image_content)

        # Perform text detection
        response = self.client.text_detection(image=image)

        # Check for errors
        if response.error.message:
            raise Exception(f"Vision API Error: {response.error.message}")

        # Get full text (first annotation contains all text)
        texts = response.text_annotations
        if not texts:
            return ""

        return texts[0].description

    def extract_patient_name(self, image_content: bytes) -> dict:
        """
        Extract patient name from a prescription image.

        The function looks for common patterns like:
        - "Patient Name: John Doe"
        - "Patient: John Doe"
        - "Name: John Doe"
        - "Pt Name: John Doe"

        Args:
            image_content: Raw bytes of the image

        Returns:
            Dictionary with extracted data:
            {
                "patient_name": "John Doe" or None,
                "full_text": "Complete extracted text",
                "confidence": "high" | "medium" | "low"
            }
        """
        # Extract all text from image
        full_text = self.extract_text_from_image(image_content)

        if not full_text:
            return {
                "patient_name": None,
                "full_text": "",
                "confidence": "low",
                "message": "No text detected in image"
            }

        # Try to find patient name with various patterns
        patient_name = None
        confidence = "low"

        # Pattern 1: "Patient Name: <name>" or "Patient Name - <name>"
        patterns = [
            r"Patient\s*Name\s*[:\-]\s*([A-Za-z\s\.]+?)(?:\n|$|Date|Age|DOB|Gender|Address|Phone)",
            r"Pt\.?\s*Name\s*[:\-]\s*([A-Za-z\s\.]+?)(?:\n|$|Date|Age|DOB|Gender|Address|Phone)",
            r"Patient\s*[:\-]\s*([A-Za-z\s\.]+?)(?:\n|$|Date|Age|DOB|Gender|Address|Phone)",
            r"Name\s*[:\-]\s*([A-Za-z\s\.]+?)(?:\n|$|Date|Age|DOB|Gender|Address|Phone)",
            r"Name\s+of\s+Patient\s*[:\-]\s*([A-Za-z\s\.]+?)(?:\n|$|Date|Age|DOB)",
        ]

        for i, pattern in enumerate(patterns):
            match = re.search(pattern, full_text, re.IGNORECASE | re.MULTILINE)
            if match:
                patient_name = match.group(1).strip()
                # Clean up the name
                patient_name = self._clean_name(patient_name)
                # First patterns are more specific, so higher confidence
                confidence = "high" if i < 2 else "medium"
                break

        return {
            "patient_name": patient_name,
            "full_text": full_text,
            "confidence": confidence,
            "message": "Patient name extracted successfully" if patient_name else "Could not find patient name pattern"
        }

    def _clean_name(self, name: str) -> str:
        """
        Clean up extracted name by removing extra whitespace and invalid characters.
        """
        if not name:
            return ""

        # Remove extra whitespace
        name = " ".join(name.split())

        # Remove trailing punctuation
        name = name.rstrip(".,;:")

        # Remove any numbers that might have been captured
        name = re.sub(r'\d+', '', name).strip()

        # Capitalize properly
        name = name.title()

        return name


# Singleton instance for easy import
ocr_service = OCRService()
