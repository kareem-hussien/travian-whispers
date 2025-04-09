/**
 * Travian Connection Verification JavaScript
 * Handles the verification of Travian account connection
 */

document.addEventListener('DOMContentLoaded', function() {
    // Get the verify connection button
    const verifyBtn = document.getElementById('verifyConnectionBtn');
    
    // If the button exists, add click event listener
    if (verifyBtn) {
        verifyBtn.addEventListener('click', verifyConnection);
    }
});

/**
 * Verify the connection to the Travian account
 */
function verifyConnection() {
    // Get button reference
    const verifyBtn = document.getElementById('verifyConnectionBtn');
    
    // Show loading state
    verifyBtn.disabled = true;
    verifyBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Verifying...';
    
    // Get CSRF token from meta tag or form
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || 
                      document.querySelector('input[name="csrf_token"]')?.value;
    
    // Get the credentials from the form
    const username = document.getElementById('travian_username').value;
    const password = document.getElementById('travian_password').value;
    const server = document.getElementById('travian_server').value;
    
    // Check if we have credentials
    if (!username || !password) {
        showConnectionResult(false, 'Please enter your Travian username and password first');
        verifyBtn.disabled = false;
        verifyBtn.innerHTML = '<i class="bi bi-check-circle me-2"></i>Verify Connection';
        return;
    }
    
    // Create verification modal to show progress
    showVerificationModal();
    
    // Make API request to verify connection
    fetch('/api/user/travian/verify-connection', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrfToken || ''
        },
        body: JSON.stringify({
            username: username,
            password: password === '********' ? null : password, // null means use existing password
            server: server
        })
    })
    .then(response => response.json())
    .then(data => {
        // Update modal with result
        updateVerificationModal(data.success, data.message, data.villages_count);
        
        // Reset button state
        verifyBtn.disabled = false;
        verifyBtn.innerHTML = '<i class="bi bi-check-circle me-2"></i>Verify Connection';
        
        // If successful, refresh the page after 3 seconds
        if (data.success) {
            setTimeout(() => {
                window.location.reload();
            }, 3000);
        }
    })
    .catch(error => {
        console.error('Verification error:', error);
        
        // Update modal with error
        updateVerificationModal(false, 'An error occurred during verification. Please try again.');
        
        // Reset button state
        verifyBtn.disabled = false;
        verifyBtn.innerHTML = '<i class="bi bi-check-circle me-2"></i>Verify Connection';
    });
}

/**
 * Show verification modal with progress indicator
 */
function showVerificationModal() {
    // Check if modal already exists
    let modal = document.getElementById('verificationModal');
    
    // If not, create it
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'verificationModal';
        modal.className = 'modal fade';
        modal.setAttribute('tabindex', '-1');
        modal.setAttribute('aria-labelledby', 'verificationModalLabel');
        modal.setAttribute('aria-hidden', 'true');
        
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="verificationModalLabel">Verifying Travian Connection</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div id="verificationProgress">
                            <div class="text-center mb-3">
                                <div class="spinner-border text-primary" role="status">
                                    <span class="visually-hidden">Loading...</span>
                                </div>
                            </div>
                            <p class="text-center" id="verificationStatus">
                                Connecting to Travian servers and verifying your account credentials...
                            </p>
                            <div class="progress">
                                <div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" 
                                     style="width: 50%" aria-valuenow="50" aria-valuemin="0" aria-valuemax="100"></div>
                            </div>
                        </div>
                        
                        <div id="verificationSuccess" class="d-none">
                            <div class="text-center mb-3">
                                <i class="bi bi-check-circle-fill text-success" style="font-size: 3rem;"></i>
                            </div>
                            <div class="alert alert-success">
                                <p class="mb-0" id="verificationSuccessMessage">Your Travian account has been successfully connected!</p>
                                <div id="villagesInfo" class="mt-2 d-none">
                                    <p class="mb-0">
                                        <i class="bi bi-buildings me-2"></i>
                                        <span id="villagesCount">0</span> villages detected in your account
                                    </p>
                                </div>
                            </div>
                            <p class="text-center text-muted">The page will refresh in a moment...</p>
                        </div>
                        
                        <div id="verificationError" class="d-none">
                            <div class="text-center mb-3">
                                <i class="bi bi-x-circle-fill text-danger" style="font-size: 3rem;"></i>
                            </div>
                            <div class="alert alert-danger">
                                <p class="mb-0" id="verificationErrorMessage">Unable to connect to your Travian account.</p>
                            </div>
                            <p class="text-center text-muted">Please check your credentials and try again.</p>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        `;
        
        // Add to document
        document.body.appendChild(modal);
    }
    
    // Reset modal state to show progress
    document.getElementById('verificationProgress').classList.remove('d-none');
    document.getElementById('verificationSuccess').classList.add('d-none');
    document.getElementById('verificationError').classList.add('d-none');
    
    // Show the modal
    const modalInstance = new bootstrap.Modal(modal);
    modalInstance.show();
}

/**
 * Update verification modal with result
 * @param {boolean} success - Whether verification was successful
 * @param {string} message - Result message
 * @param {number} villagesCount - Number of villages detected (if successful)
 */
function updateVerificationModal(success, message, villagesCount) {
    // Hide progress
    document.getElementById('verificationProgress').classList.add('d-none');
    
    if (success) {
        // Show success
        const successDiv = document.getElementById('verificationSuccess');
        successDiv.classList.remove('d-none');
        
        // Update success message
        document.getElementById('verificationSuccessMessage').textContent = message;
        
        // Update villages count if available
        if (villagesCount !== undefined && villagesCount !== null) {
            const villagesInfo = document.getElementById('villagesInfo');
            villagesInfo.classList.remove('d-none');
            
            const countEl = document.getElementById('villagesCount');
            countEl.textContent = villagesCount;
            
            // Add proper pluralization
            const villagesText = villagesCount === 1 ? 'village' : 'villages';
            countEl.nextElementSibling.textContent = ` ${villagesText} detected in your account`;
        }
    } else {
        // Show error
        const errorDiv = document.getElementById('verificationError');
        errorDiv.classList.remove('d-none');
        
        // Update error message
        document.getElementById('verificationErrorMessage').textContent = message;
    }
}

/**
 * Show an alert message on the page
 * @param {boolean} success - Whether the message is for success or error
 * @param {string} message - The message to display
 */
function showConnectionResult(success, message) {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${success ? 'success' : 'danger'} alert-dismissible fade show mt-3`;
    alertDiv.setAttribute('role', 'alert');
    
    alertDiv.innerHTML = `
        <i class="bi bi-${success ? 'check-circle' : 'exclamation-triangle'}-fill me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add to the page
    const connectionStatusSection = document.querySelector('.dashboard-card:nth-child(1)');
    connectionStatusSection.appendChild(alertDiv);
    
    // Auto dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => alertDiv.remove(), 150);
    }, 5000);
}
