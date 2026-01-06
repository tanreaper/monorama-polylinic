"""
Firestore Service - Manage patients and prescriptions
"""

from google.cloud import firestore
from datetime import datetime, timezone
from typing import Optional, List, Dict
import os
import uuid

class FirestoreService:
    def __init__(self):
        """ Initialize Firestore client """
        self.use_mock = os.getenv("USE_MOCK_FIRESTORE", "false").lower() == "true"

        if not self.use_mock:
            self.db = firestore.Client()
        else:
            self.db = None
            # Mock storage for local development
            self.mock_patients = {}
            self.mock_prescriptions = {}
    
    def find_patient_by_file_id(self, file_id: str) -> Optional[Dict]:
        """
        Docstring for find_patient_by_file_id
        
        :param self: FirestoreService instance
        :param file_id: The file ID to search for (e.g., "ID-061")
        :type file_id: str
        :return: Patient dictionary if found, None if not found
        :rtype: Dict | None
        """

        # MOCK MODE: Search in mock_patients dictionary
        if self.use_mock:
            for patient in self.mock_patients.values():
                if patient.get('file_id') == file_id:
                    return patient
            return None
        
        # REAL MODE: Query Firestore
        patients = self.db.collection('patients').where('file_id', '==', file_id).limit(1).get()

        if patients:
            # Convert Firestore document to dictionary
            patient_data = patients[0].to_dict()
            # Add the document ID as patient_id
            patient_data['patient_id'] = patients[0].id
            return patient_data
    
        return None
    
    def find_patient_by_phone(self, phone: str) -> Optional[Dict]:
        """
        Docstring for find_patient_by_phone
        
        :param self: FirestoreService instance
        :param phone: Phone Number of the patient
        :type phone: str
        :return: Patient dictionary if found, None if not found
        :rtype: Dict | None
        """
        if self.use_mock:
            for patient in self.mock_patients.values():
                if patient.get('phone') == phone:
                    return patient
            return None
        
        # REAL MODE: Query Firestore
        patients = self.db.collection('patients').where('phone', '==', phone).limit(1).get()

        if patients:
            # Convert Firestore document to dictionary
            patient_data = patients[0].to_dict()
            # Add the document ID as patient_id
            patient_data['patient_id'] = patients[0].id
            return patient_data
    
        return None
    
    def create_patient(self, name: str, file_id: Optional[str] = None, phone: Optional[str] = None, needs_review: bool = False) -> str: 
        """
        Create a new patient record
        
        :param self: FirestoreService instance
        :param name: Patient name
        :type name: str
        :param file_id: File ID (can be None for old prescription)
        :type file_id: Optional[str]
        :param phone: Phone number (can be None)
        :type phone: Optional[str]
        :param needs_review: Flag for orphan records needing file_id/phone later
        :type needs_review: bool
        :return: The newly created patient_id
        :rtype: str
        """
        # Generate unique ID
        patient_id = str(uuid.uuid4())

        # Create patient data dictionary
        patient_data = {
            'name': name,
            'file_id': file_id,
            'phone': phone,
            'needs_review': needs_review,
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }

        # MOCK MODE: Store in memory
        if self.use_mock:
            patient_data['patient_id'] = patient_id
            self.mock_patients[patient_id] = patient_data
            return patient_id
        
        # REAL MODE: Save to Firestore
        doc_ref = self.db.collection('patients').document(patient_id)
        doc_ref.set(patient_data)

        return patient_id
        
    def update_patient(self, patient_id: str, updates: Dict) -> None:
        """
        Update patient record
        
        :param self: FirestoreService instance
        :param patient_id: Patient ID to update
        :type patient_id: str
        :param updates: Dictionary of fields to update(e.g., {'file_id': 'ID-061, 'phone': '+91-123'})
        :type updates: Dict
        :return: None
        :rtype: None
        """

        # Always update the updated_at timestamp
        updates['updated_at'] = datetime.now(timezone.utc)

        # MOCK MODE: Update in memory
        if self.use_mock:
            if patient_id in self.mock_patients:
                self.mock_patients[patient_id].update(updates)
            return
        # REAL MODE: Update in Firestore
        self.db.collection('patients').document(patient_id).update(updates)

    def list_all_patients(self, order_by: str = 'name') -> List[Dict]:
        """
        List all patients sorted alphabetically
        
        :param self: FirestoreService instance
        :param order_by: Field to sort by (default: 'name')
        :type order_by: str
        :return: List of patient dictionaries
        :rtype: List[Dict]
        """

        if self.use_mock:
            patients = list(self.mock_patients.values())
            return sorted(patients, key=lambda p: p.get(order_by, ''))
        
        patients = self.db.collection('patients').order_by(order_by).get()
        results = []
        for patient in patient:
            patient_data = patient.to_dict()
            patient_data['patient_id'] = patient.id
            results.appent(patient_data)
        return results

def list_patients_needing_review(self) -> List[Dict]:
    """
    Get all patients that need file_id/phone added (old prescriptions)
    
    :param self: FirestoreService instance
    :return: List of patient dictionaries needing review
    :rtype: List[Dict]
    """
    if self.use_mock:
        return [p for p in self.mock_patients.values() if p.get('needs_review')]
    
    patients = self.db.collection('patients').where('needs_review', '==', True).get()
    results = []
    for patient in patients:
        patient_data = patient.to_dict()
        patient_data['patient_id'] = patient.id
        results.append(patient_data)
    return results


# ============ PRESCRIPTION OPERATIONS ============

def create_prescription(
    self,
    patient_id: str,
    file_id: Optional[str],
    patient_name: str,
    date: Optional[str],
    age: Optional[int],
    sex: Optional[str],
    weight: Optional[str],
    image_url: str,
    blob_name: str,
    ocr_confidence: str = "medium",
    needs_review: bool = False
) -> str:
    """
    Create a new prescription record
    
    :param self: FirestoreService instance
    :param patient_id: Patient ID this prescription belongs to
    :type patient_id: str
    :param file_id: File ID (denormalized from patient)
    :type file_id: Optional[str]
    :param patient_name: Patient name
    :type patient_name: str
    :param date: Prescription date
    :type date: Optional[str]
    :param age: Patient age
    :type age: Optional[int]
    :param sex: Patient sex (M/F)
    :type sex: Optional[str]
    :param weight: Patient weight
    :type weight: Optional[str]
    :param image_url: Signed URL to prescription image
    :type image_url: str
    :param blob_name: Cloud Storage blob name
    :type blob_name: str
    :param ocr_confidence: OCR confidence level
    :type ocr_confidence: str
    :param needs_review: Flag for old prescriptions
    :type needs_review: bool
    :return: The newly created prescription_id
    :rtype: str
    """
    prescription_id = str(uuid.uuid4())
    
    prescription_data = {
        'patient_id': patient_id,
        'file_id': file_id,
        'patient_name': patient_name,
        'date': date,
        'age': age,
        'sex': sex,
        'weight': weight,
        'image_url': image_url,
        'blob_name': blob_name,
        'ocr_confidence': ocr_confidence,
        'needs_review': needs_review,
        'uploaded_at': datetime.now(timezone.utc)
    }
    
    if self.use_mock:
        prescription_data['prescription_id'] = prescription_id
        self.mock_prescriptions[prescription_id] = prescription_data
        return prescription_id
    
    doc_ref = self.db.collection('prescriptions').document(prescription_id)
    doc_ref.set(prescription_data)
    
    return prescription_id


def get_prescriptions_by_patient(self, patient_id: str) -> List[Dict]:
    """
    Get all prescriptions for a patient
    
    :param self: FirestoreService instance
    :param patient_id: Patient ID
    :type patient_id: str
    :return: List of prescription dictionaries
    :rtype: List[Dict]
    """
    if self.use_mock:
        return [p for p in self.mock_prescriptions.values() if p.get('patient_id') == patient_id]
    
    prescriptions = self.db.collection('prescriptions').where('patient_id', '==', patient_id).order_by('uploaded_at', direction=firestore.Query.DESCENDING).get()
    results = []
    for prescription in prescriptions:
        prescription_data = prescription.to_dict()
        prescription_data['prescription_id'] = prescription.id
        results.append(prescription_data)
    return results


def update_prescriptions_file_id(self, patient_id: str, new_file_id: str) -> int:
    """
    Update file_id for all prescriptions of a patient
    (Used when adding file_id to old prescriptions)
    
    :param self: FirestoreService instance
    :param patient_id: Patient ID
    :type patient_id: str
    :param new_file_id: New file ID to set
    :type new_file_id: str
    :return: Number of prescriptions updated
    :rtype: int
    """
    if self.use_mock:
        count = 0
        for prescription in self.mock_prescriptions.values():
            if prescription.get('patient_id') == patient_id:
                prescription['file_id'] = new_file_id
                count += 1
        return count
    
    prescriptions = self.db.collection('prescriptions').where('patient_id', '==', patient_id).get()
    count = 0
    for prescription in prescriptions:
        prescription.reference.update({'file_id': new_file_id})
        count += 1
    return count


# Singleton instance
firestore_service = FirestoreService()

    
    






        

        
