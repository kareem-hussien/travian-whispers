/**
 * Travian Verification JavaScript
 * Handles manual connection verification and UI updates
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the verify connection button if it exists
    const verifyBtn = document.getElementById('verifyConnectionBtn');
    if (verifyBtn) {
        verifyBtn.addEventListener('click', verifyTravianConnection);
    }
});

/**
 * Verify Travian connection with current credentials
 */
function verifyTravianConnection() {
    // Get credentials from form
    const travianUsername = document.getElementById('travian_username').value;
    const travianPassword = document.getElementById('travian_password').value;
    const travianServer = document.getElementById('travian_server').value;
    
    // Validate credentials
    if (!travianUsername || !travianPassword) {
        alert('Please enter your Travian username and password first.');
        return;
    }
    
    // Update button state
    const verifyBtn = document.getElementById('verifyConnectionBtn');
    const originalText = verifyBtn.innerHTML;
    verifyBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Verifying...';
    verifyBtn.disabled = true;
    
    // Get CSRF token
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || 
                      document.querySelector('input[name="csrf_token"]')?.value;
    
    // Call API to verify connection
    fetch('/api/user/travian/verify-connection', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrfToken || '',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            username: travianUsername,
            password: travianPassword,
            server: travianServer
        })
    })
    .then(response => response.json())
    .then(data => {
        // Update UI based on response
        if (data.success) {
            // Show success message
            showVerificationSuccess(data);
            
            // Initiate village extraction if connection was successful
            initiateVillageExtraction();
        } else {
            // Show error message
            showVerificationError(data.message || 'Failed to verify connection');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showVerificationError('An error occurred during verification');
    })
    .finally(() => {
        // Reset button state
        verifyBtn.innerHTML = originalText;
        verifyBtn.disabled = false;
    });
}

/**
 * Show success message after verification
 */
function showVerificationSuccess(data) {
    // Create success alert
    const alert = document.createElement('div');
    alert.className = 'alert alert-success mt-3';
    alert.innerHTML = `
        <i class="bi bi-check-circle-fill me-2"></i>
        <strong>Connection verified!</strong> Your Travian account is working correctly.
        ${data.villages_count ? `<div class="mt-2"><i class="bi bi-buildings me-2"></i><strong>${data.villages_count}</strong> villages detected.</div>` : ''}
    `;
    
    // Replace any existing alerts
    const existingAlerts = document.querySelectorAll('.dashboard-card .alert-success, .dashboard-card .alert-danger');
    existingAlerts.forEach(el => el.remove());
    
    // Find the connection status section
    const statusSection = document.querySelector('.dashboard-card');
    if (statusSection) {
        statusSection.appendChild(alert);
    }
    
    // Update status indicator
    const statusIndicator = document.querySelector('.dashboard-card .badge');
    if (statusIndicator) {
        statusIndicator.className = 'badge bg-success me-2';
        statusIndicator.textContent = 'Connected';
        statusIndicator.nextElementSibling.textContent = 'Your account is connected and working';
    }
}

/**
 * Show error message after verification
 */
function showVerificationError(message) {
    // Create error alert
    const alert = document.createElement('div');
    alert.className = 'alert alert-danger mt-3';
    alert.innerHTML = `
        <i class="bi bi-exclamation-triangle-fill me-2"></i>
        <strong>Connection failed!</strong> ${message}
    `;
    
    // Replace any existing alerts
    const existingAlerts = document.querySelectorAll('.dashboard-card .alert-success, .dashboard-card .alert-danger');
    existingAlerts.forEach(el => el.remove());
    
    // Find the connection status section
    const statusSection = document.querySelector('.dashboard-card');
    if (statusSection) {
        statusSection.appendChild(alert);
    }
}

/**
 * Initiate village extraction after successful connection
 */
function initiateVillageExtraction() {
    // Create extraction notification
    const notice = document.createElement('div');
    notice.className = 'alert alert-info mt-3';
    notice.innerHTML = `
        <div class="d-flex align-items-center">
            <div class="spinner-border spinner-border-sm text-info me-2" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <div>Extracting your villages from Travian...</div>
        </div>
    `;
    
    // Find the connection status section
    const statusSection = document.querySelector('.dashboard-card');
    if (statusSection) {
        statusSection.appendChild(notice);
    }
    
    // Get CSRF token
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || 
                      document.querySelector('input[name="csrf_token"]')?.value;
    
    // Call API to extract villages
    fetch('/api/user/villages/extract', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrfToken || '',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({})
    })
    .then(response => response.json())
    .then(data => {
        // Remove the extraction notification
        notice.remove();
        
        // Show result
        if (data.success) {
            const villagesCount = data.data ? data.data.length : 0;
            const resultNotice = document.createElement('div');
            resultNotice.className = 'alert alert-success mt-3';
            resultNotice.innerHTML = `
                <i class="bi bi-check-circle-fill me-2"></i>
                <div><strong>Villages extracted successfully!</strong></div>
                <div class="mt-1">
                    <i class="bi bi-buildings me-2"></i>
                    <strong>${villagesCount}</strong> villages found in your Travian account.
                </div>
                <div class="mt-2">
                    <a href="/dashboard/villages" class="btn btn-sm btn-outline-success">
                        <i class="bi bi-buildings me-1"></i>View Villages
                    </a>
                </div>
            `;
            
            // Find the connection status section
            const statusSection = document.querySelector('.dashboard-card');
            if (statusSection) {
                statusSection.appendChild(resultNotice);
            }
        } else {
            // Show error
            const errorNotice = document.createElement('div');
            errorNotice.className = 'alert alert-warning mt-3';
            errorNotice.innerHTML = `
                <i class="bi bi-exclamation-triangle-fill me-2"></i>
                <div><strong>Village extraction failed.</strong> ${data.message || 'Unknown error'}</div>
                <div class="mt-2">
                    <a href="/dashboard/villages" class="btn btn-sm btn-outline-primary">
                        <i class="bi bi-buildings me-1"></i>Try Manual Extraction
                    </a>
                </div>
            `;
            
            // Find the connection status section
            const statusSection = document.querySelector('.dashboard-card');
            if (statusSection) {
                statusSection.appendChild(errorNotice);
            }
        }
    })
    .catch(error => {
        // Remove the extraction notification
        notice.remove();
        
        console.error('Error:', error);
        const errorNotice = document.createElement('div');
        errorNotice.className = 'alert alert-danger mt-3';
        errorNotice.innerHTML = `
            <i class="bi bi-exclamation-triangle-fill me-2"></i>
            <div><strong>Error during village extraction:</strong> An unexpected error occurred.</div>
            <div class="mt-2">
                <a href="/dashboard/villages" class="btn btn-sm btn-outline-primary">
                    <i class="bi bi-buildings me-1"></i>Try Manual Extraction
                </a>
            </div>
        `;
        
        // Find the connection status section
        const statusSection = document.querySelector('.dashboard-card');
        if (statusSection) {
            statusSection.appendChild(errorNotice);
        }
    });
}
