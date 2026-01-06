// API Base URL
const API_BASE = window.location.origin;

// Global state
let authToken = null;
let currentStream = null;
let capturedImageBlob = null;
let currentPatient = null;

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    // Check if user is already logged in
    authToken = localStorage.getItem('authToken');
    if (authToken) {
        verifyTokenAndShowDashboard();
    }

    // Setup login form
    document.getElementById('login-form').addEventListener('submit', handleLogin);
});

// ============ Authentication ============

async function handleLogin(e) {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    try {
        const response = await fetch(`${API_BASE}/api/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            authToken = data.access_token;
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('username', data.username);
            showDashboard();
            document.getElementById('login-form').reset();
            hideError('login-error');
        } else {
            showError('login-error', data.detail || 'Login failed');
        }
    } catch (error) {
        showError('login-error', 'Connection error. Please try again.');
        console.error('Login error:', error);
    }
}

async function verifyTokenAndShowDashboard() {
    try {
        const response = await fetch(`${API_BASE}/api/auth/verify`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            showDashboard();
        } else {
            logout();
        }
    } catch (error) {
        logout();
    }
}

function logout() {
    authToken = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('username');
    showScreen('login-screen');
    document.getElementById('user-info').classList.add('hidden');
}

// ============ Screen Navigation ============

function showScreen(screenId) {
    // Hide all screens
    const screens = ['login-screen', 'dashboard-screen', 'camera-screen', 'patients-screen', 'prescriptions-screen'];
    screens.forEach(id => {
        document.getElementById(id).classList.add('hidden');
    });

    // Show requested screen
    document.getElementById(screenId).classList.remove('hidden');
}

function showDashboard() {
    const username = localStorage.getItem('username');
    const userInfo = document.getElementById('user-info');
    userInfo.textContent = `Logged in as: ${username}`;
    userInfo.classList.remove('hidden');

    showScreen('dashboard-screen');
}

function showCamera() {
    showScreen('camera-screen');
    hideAlert('upload-alert');
    document.getElementById('camera-container').classList.add('hidden');
    document.getElementById('preview-container').classList.add('hidden');
    document.getElementById('patient-name-input').value = ''; 
}


function showPatients() {
    showScreen('patients-screen');
    loadPatients();
}

// ============ Camera Functions ============

async function startCamera() {
    try {
        // Stop any existing stream
        if (currentStream) {
            currentStream.getTracks().forEach(track => track.stop());
        }

        // Request camera access
        currentStream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'environment' } // Use back camera on mobile
        });

        const video = document.getElementById('camera-feed');
        video.srcObject = currentStream;

        document.getElementById('camera-container').classList.remove('hidden');
        document.getElementById('preview-container').classList.add('hidden');
    } catch (error) {
        showAlert('upload-alert', 'Camera access denied. Please use file upload.', 'error');
        console.error('Camera error:', error);
    }
}

function capturePhoto() {
    const video = document.getElementById('camera-feed');
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);

    // Convert to blob
    canvas.toBlob(blob => {
        capturedImageBlob = blob;
        displayPreview(canvas.toDataURL());
        stopCamera();
    }, 'image/jpeg', 0.9);
}

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        capturedImageBlob = file;
        const reader = new FileReader();
        reader.onload = (e) => displayPreview(e.target.result);
        reader.readAsDataURL(file);
    }
}

function displayPreview(imageDataUrl) {
    document.getElementById('preview-image').src = imageDataUrl;
    document.getElementById('preview-container').classList.remove('hidden');
    document.getElementById('camera-container').classList.add('hidden');
    document.getElementById('ocr-result').textContent = 'Analyzing prescription...';

    // Extract patient name using OCR
    extractPatientName();
}

function stopCamera() {
    if (currentStream) {
        currentStream.getTracks().forEach(track => track.stop());
        currentStream = null;
    }
}

function retakePhoto() {
    capturedImageBlob = null;
    document.getElementById('preview-container').classList.add('hidden');
    document.getElementById('patient-name-input').value = '';  // ADD THIS LINE
    startCamera();
}


// ============ OCR & Upload ============

async function extractPatientName() {
    if (!capturedImageBlob) {
        return;
    }

   const formData = new FormData();
   formData.append('file', capturedImageBlob, 'prescription.jpg');

    try {
        const response = await fetch(`${API_BASE}/api/ocr/extract-name`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            },
            body: formData
        });

        const data = await response.json();

        if (response.ok && data.success) {
            const patientName = data.data.patient_name;
            const confidence = data.data.confidence;

            // Get the input field
            const nameInput = document.getElementById('patient-name-input');
            const resultEl = document.getElementById('ocr-result');

            if (!nameInput) {
                console.error('ERROR: patient-name-input element not found!');
                return;
            }

            if (patientName) {
                // SUCCESS: OCR found a name
                // Pre-fill the input field with extracted name
                nameInput.value = patientName;

                // Show success message
                resultEl.innerHTML = `
                    <div>
                        <i class="fas fa-check-circle"></i>
                        <strong>Name extracted successfully!</strong><br>
                        <small>Confidence: ${confidence} - You can edit below if needed</small>
                    </div>
                `;
                resultEl.className = 'alert alert-success';
            } else {
                // OCR FAILED: Couldn't find name
                // Leave input field empty
                nameInput.value = '';

                // Show warning - user must type manually
                resultEl.innerHTML = `
                    <div>
                        <i class="fas fa-exclamation-triangle"></i>
                        <strong>Could not extract patient name</strong><br>
                        <small>Please enter the name manually below</small>
                    </div>
                `;
                resultEl.className = 'alert alert-info';

                // Focus on input field so user can type immediately
                nameInput.focus();
            }
        } else {
            showOcrWarning();
        }
    } catch (error) {
        showOcrWarning();
        console.error('OCR error:', error);
    }
}

function showOcrWarning() {
    const nameInput = document.getElementById('patient-name-input');
    const resultEl = document.getElementById('ocr-result');
    
    // Leave input field empty
    nameInput.value = '';
    
    // Show warning
    resultEl.innerHTML = `
        <div>
            <i class="fas fa-exclamation-triangle"></i>
            <strong>Could not extract patient name</strong><br>
            <small>Please enter the name manually below</small>
        </div>
    `;
    resultEl.className = 'alert alert-info';
    
    // Focus on input field
    nameInput.focus();
}



async function uploadPrescription() {
    if (!capturedImageBlob) {
        showAlert('upload-alert', 'No image captured', 'error');
        return;
    }
    // Get patient name from input field
    const patientNameInput = document.getElementById('patient-name-input');

    if (!patientNameInput) {
        console.error('ERROR: patient-name-input element not found in uploadPrescription!');
        showAlert('upload-alert', 'Error: Name input field not found', 'error');
        return;
    }

    const patientName = patientNameInput.value.trim();

    // Validate: name must not be empty
    if (!patientName) {
        showAlert('upload-alert', 'Please enter a patient name', 'error');
        patientNameInput.focus();
        return;
    }

    // Validate: name must be at least 2 characters
    if (patientName.length < 2) {
        showAlert('upload-alert', 'Patient name must be at least 2 characters', 'error');
        patientNameInput.focus();
        return;
    }

    const formData = new FormData();
    formData.append('file', capturedImageBlob, 'prescription.jpg');
    formData.append('manual_name', patientName);

    try {
        showAlert('upload-alert', 'Uploading prescription...', 'info');

        const response = await fetch(`${API_BASE}/api/prescriptions/upload`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            },
            body: formData
        });

        const data = await response.json();

        if (response.ok && data.success) {
            showAlert('upload-alert', 'Prescription uploaded successfully for ' + data.ocr.patient_name + '!', 'success');

            // Reset after 2 seconds
            setTimeout(() => {
                capturedImageBlob = null;
                showDashboard();
            }, 2000);
        } else {
            showAlert('upload-alert', data.detail || 'Upload failed', 'error');
        }
    } catch (error) {
        showAlert('upload-alert', 'Upload failed. Please try again.', 'error');
        console.error('Upload error:', error);
    }
}

// ============ Patients List ============

async function loadPatients() {
    document.getElementById('patients-loading').classList.remove('hidden');
    document.getElementById('patients-list').classList.add('hidden');

    try {
        const response = await fetch(`${API_BASE}/api/prescriptions/patients`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        const data = await response.json();

        if (response.ok && data.success) {
            displayPatients(data.patients);
        } else {
            throw new Error('Failed to load patients');
        }
    } catch (error) {
        document.getElementById('patients-loading').innerHTML = '<p>Failed to load patients</p>';
        console.error('Load patients error:', error);
    }
}

function displayPatients(patients) {
    const list = document.getElementById('patients-list');
    list.innerHTML = '';

    if (patients.length === 0) {
        list.innerHTML = '<li class="patient-item">No patients found</li>';
    } else {
        patients.forEach(patient => {
            const li = document.createElement('li');
            li.className = 'patient-item';

            const nameSpan = document.createElement('span');
            nameSpan.className = 'patient-name';
            nameSpan.textContent = patient.replace(/_/g, ' ');

            const arrowSpan = document.createElement('span');
            arrowSpan.textContent = '→';

            li.appendChild(nameSpan);
            li.appendChild(arrowSpan);
            li.onclick = () => viewPatientPrescriptions(patient);
            list.appendChild(li);
        });
    }

    document.getElementById('patients-loading').classList.add('hidden');
    list.classList.remove('hidden');
}

// ============ Patient Prescriptions ============

async function viewPatientPrescriptions(patientName) {
    currentPatient = patientName;
    showScreen('prescriptions-screen');

    document.getElementById('patient-title').textContent = patientName.replace(/_/g, ' ').toUpperCase();
    document.getElementById('prescriptions-loading').classList.remove('hidden');
    document.getElementById('prescriptions-grid').classList.add('hidden');

    try {
        const response = await fetch(`${API_BASE}/api/prescriptions/patients/${patientName}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        const data = await response.json();

        if (response.ok && data.success) {
            displayPrescriptions(data.prescriptions);
        } else {
            throw new Error('Failed to load prescriptions');
        }
    } catch (error) {
        document.getElementById('prescriptions-loading').innerHTML = '<p>Failed to load prescriptions</p>';
        console.error('Load prescriptions error:', error);
    }
}

function displayPrescriptions(prescriptions) {
    const grid = document.getElementById('prescriptions-grid');
    grid.innerHTML = '';

    if (prescriptions.length === 0) {
        grid.innerHTML = '<p>No prescriptions found</p>';
    } else {
        prescriptions.forEach(prescription => {
            const card = document.createElement('div');
            card.className = 'prescription-card';

            const img = document.createElement('img');
            img.src = prescription.url;
            img.alt = 'Prescription';
            img.onclick = () => window.open(prescription.url, '_blank');

            card.appendChild(img);
            grid.appendChild(card);
        });
    }

    document.getElementById('prescriptions-loading').classList.add('hidden');
    grid.classList.remove('hidden');
}

// ============ Utility Functions ============

function showError(elementId, message) {
    const el = document.getElementById(elementId);
    el.textContent = message;
    el.classList.remove('hidden');
}

function hideError(elementId) {
    document.getElementById(elementId).classList.add('hidden');
}

function showAlert(elementId, message, type) {
    if (type === undefined) type = 'info';
    const el = document.getElementById(elementId);
    el.textContent = message;
    el.className = 'alert alert-' + type;
    el.classList.remove('hidden');
}

function hideAlert(elementId) {
    document.getElementById(elementId).classList.add('hidden');
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    stopCamera();
});
