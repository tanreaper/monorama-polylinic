"""
Storage Service - Upload and manage prescription images in Google Cloud Storage
"""

from google.cloud import storage
from datetime import timedelta
from google.auth import impersonated_credentials
import google.auth
import os
import uuid


class StorageService:
    def __init__(self, bucket_name: str = None):
        """Initialize the Storage client"""
        self.use_mock = os.getenv("USE_MOCK_STORAGE", "false").lower() == "true"

        if not self.use_mock:
            self.client = storage.Client()
            self.bucket_name = bucket_name or os.environ.get(
                "GCP_BUCKET_NAME",
                "monorama-polyclinic-prescriptions"
            )
            self.bucket = self.client.bucket(self.bucket_name)
            self.service_account_email = "polyclinic-backend@monorama-polyclinic.iam.gserviceaccount.com"
        else:
            self.client = None
            self.bucket_name = "mock-bucket"
            self.bucket = None
            self.service_account_email = None
            # Store mock data in memory
            self.mock_storage = {}

    def _get_signing_credentials(self):
        """Get credentials for signing URLs using IAM"""
        credentials, project = google.auth.default()

        # Create impersonated credentials for signing
        signing_credentials = impersonated_credentials.Credentials(
            source_credentials=credentials,
            target_principal=self.service_account_email,
            target_scopes=['https://www.googleapis.com/auth/cloud-platform'],
        )

        return signing_credentials

    def upload_prescription(
        self,
        image_content: bytes,
        patient_name: str,
        file_extension: str = "jpg"
    ) -> dict:
        """
        Upload a prescription image to Cloud Storage.

        Files are organized by patient name for easy retrieval.
        Format: prescriptions/{patient_name}/{unique_id}.{ext}

        Args:
            image_content: Raw bytes of the image
            patient_name: Extracted patient name (used for organization)
            file_extension: File type (jpg, png, etc.)

        Returns:
            Dictionary with upload details

        """
        # Clean patient name for use in path
        clean_name = self._sanitize_filename(patient_name)

        # Generate unique filename
        unique_id = str(uuid.uuid4())[:8]
        blob_name = f"prescriptions/{clean_name}/{unique_id}.{file_extension}"

        # Mock mode: store in memory
        if self.use_mock:
            if clean_name not in self.mock_storage:
                self.mock_storage[clean_name] = []
            self.mock_storage[clean_name].append(blob_name)

            return {
                "blob_name": blob_name,
                "patient_name": patient_name,
                "clean_name": clean_name,
                "signed_url": f"https://mock-storage.local/{blob_name}",
                "bucket": self.bucket_name
            }

        # Upload to GCS
        blob = self.bucket.blob(blob_name)
        blob.upload_from_string(
            image_content,
            content_type=f"image/{file_extension}"
        )

        # Generate signed URL for viewing (valid for 7 days)
        try:
            signing_credentials = self._get_signing_credentials()
            signed_url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(days=7),
                method="GET",
                credentials=signing_credentials
            )
        except Exception as e:
            print(f"Error generating signed URL: {e}")
            # Fallback: use public URL (requires bucket to be public)
            signed_url = f"https://storage.googleapis.com/{self.bucket_name}/{blob_name}"

        return {
            "blob_name": blob_name,
            "patient_name": patient_name,
            "clean_name": clean_name,
            "signed_url": signed_url,
            "bucket": self.bucket_name
        }

    def get_signed_url(self, blob_name: str, expiration_days: int = 7) -> str:
        """
        Generate a signed URL for an existing file.

        Args:
            blob_name: Path to file in bucket
            expiration_days: How long the URL is valid

        Returns:
            Signed URL string
        """
        # Mock mode: return mock URL
        if self.use_mock:
            return f"https://mock-storage.local/{blob_name}"

        blob = self.bucket.blob(blob_name)

        try:
            signing_credentials = self._get_signing_credentials()
            return blob.generate_signed_url(
                version="v4",
                expiration=timedelta(days=expiration_days),
                method="GET",
                credentials=signing_credentials
            )
        except Exception as e:
            print(f"Error generating signed URL: {e}")
            # Fallback: use public URL
            return f"https://storage.googleapis.com/{self.bucket_name}/{blob_name}"

    def list_prescriptions_by_patient(self, patient_name: str) -> list:
        """
        List all prescriptions for a specific patient.

        Args:
            patient_name: Patient name to search for

        Returns:
            List of blob names
        """
        clean_name = self._sanitize_filename(patient_name)

        # Mock mode: return from memory
        if self.use_mock:
            return self.mock_storage.get(clean_name, [])

        prefix = f"prescriptions/{clean_name}/"

        blobs = list(self.bucket.list_blobs(prefix=prefix))

        return [blob.name for blob in blobs]

    def list_all_patients(self) -> list:
        """
        List all patient folders (sorted alphabetically).

        Returns:
            List of patient names
        """
        # Mock mode: return from memory
        if self.use_mock:
            return sorted(self.mock_storage.keys())

        # List all blobs under prescriptions/
        blobs = self.bucket.list_blobs(prefix="prescriptions/")
        # Extract unique patient names from paths
        patients = set()
        for blob in blobs:
            parts = blob.name.split("/")
            if len(parts) >= 2:
                patients.add(parts[1])

        # Return sorted list
        return sorted(patients)

    def _sanitize_filename(self, name: str) -> str:
        """
        Clean a string for use in file paths.

        - Lowercase
        - Replace spaces with underscores
        - Remove special characters
        """
        if not name:
            return "unknown"

        # Lowercase and replace spaces
        clean = name.lower().strip().replace(" ", "_")

        # Keep only alphanumeric and underscores
        clean = "".join(c for c in clean if c.isalnum() or c == "_")

        return clean or "unknown"


# Singleton instance
storage_service = StorageService()
