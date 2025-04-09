/**
 * Travian Whispers - Villages Management JavaScript
 * This file handles all the frontend interactions for the villages page
 */

document.addEventListener('DOMContentLoaded', function() {
    // Debug initialization
    console.log("Villages.js loaded and initialized");
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Extract Villages button
    const extractVillagesBtn = document.getElementById('extractVillages');
    if (extractVillagesBtn) {
        console.log("Extract Villages button found");
        extractVillagesBtn.addEventListener('click', function() {
            console.log("Extract Villages button clicked");
            showExtractModal();
        });
    } else {
        console.error("Extract Villages button not found!");
    }
    
    // Village details button events
    document.querySelectorAll('.village-details').forEach(button => {
        button.addEventListener('click', function() {
            const villageId = this.getAttribute('data-village-id');
            showVillageDetails(villageId);
        });
    });
    
    // Village edit button events
    document.querySelectorAll('.village-edit').forEach(button => {
        button.addEventListener('click', function() {
            const villageId = this.getAttribute('data-village-id');
            populateEditVillageForm(villageId);
        });
    });
    
    // Village remove button events
    document.querySelectorAll('.village-remove').forEach(button => {
        button.addEventListener('click', function() {
            const villageId = this.getAttribute('data-village-id');
            const villageName = this.getAttribute('data-village-name');
            showRemoveVillageConfirmation(villageId, villageName);
        });
    });
    
    // Save village edit
    document.getElementById('saveVillageBtn')?.addEventListener('click', function() {
        saveVillageChanges();
    });
    
    // Add village button
    document.getElementById('addVillageBtn')?.addEventListener('click', function() {
        addVillage();
    });
    
    // Confirm remove village button
    document.getElementById('confirmRemoveBtn')?.addEventListener('click', function() {
        removeVillage();
    });
    
    // Village settings form submit
    document.getElementById('villageSettingsForm')?.addEventListener('submit', function(e) {
        e.preventDefault();
        saveVillageSettings();
    });
    
    // Confirm extract villages button
    const confirmExtractBtn = document.getElementById('confirmExtractBtn');
    if (confirmExtractBtn) {
        console.log("Confirm Extract button found");
        confirmExtractBtn.addEventListener('click', function() {
            console.log("Confirm Extract button clicked");
            startVillageExtraction();
        });
    } else {
        console.error("Confirm Extract button not found!");
    }
    
    // Refresh villages button
    document.getElementById('refreshVillages')?.addEventListener('click', function() {
        refreshVillagesData();
    });
});

/**
 * Show the extract villages modal
 */
function showExtractModal() {
    console.log("Showing extract modal");
    
    // Check if modal element exists
    const modalElement = document.getElementById('extractVillagesModal');
    if (!modalElement) {
        console.error("Extract Villages Modal not found in the DOM!");
        return;
    }
    
    // Reset the modal state
    document.getElementById('extractProgress')?.classList.add('d-none');
    document.getElementById('extractResults')?.classList.add('d-none');
    document.getElementById('extractError')?.classList.add('d-none');
    
    document.getElementById('confirmExtractBtn')?.classList.remove('d-none');
    document.getElementById('extractCancelBtn')?.classList.remove('d-none');
    document.getElementById('extractDoneBtn')?.classList.add('d-none');
    
    // Check if Bootstrap is available
    if (typeof bootstrap === 'undefined') {
        console.error("Bootstrap not found! Modal cannot be displayed.");
        return;
    }
    
    // Show the modal
    try {
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
        console.log("Modal shown successfully");
    } catch (error) {
        console.error("Error showing modal:", error);
    }
}

/**
 * Start village extraction process
 */
function startVillageExtraction() {
    console.log("Starting village extraction");
    
    // Check if elements exist
    const progressElement = document.getElementById('extractProgress');
    const progressBar = document.querySelector('#extractProgress .progress-bar');
    const statusText = document.getElementById('extractStatus');
    
    if (!progressElement || !progressBar || !statusText) {
        console.error("Required DOM elements for extraction not found!");
        return;
    }
    
    // Show progress section and hide others
    progressElement.classList.remove('d-none');
    document.getElementById('extractResults')?.classList.add('d-none');
    document.getElementById('extractError')?.classList.add('d-none');
    
    // Hide/show buttons
    document.getElementById('confirmExtractBtn')?.classList.add('d-none');
    document.getElementById('extractCancelBtn')?.classList.add('d-none');
    document.getElementById('extractDoneBtn')?.classList.add('d-none');
    
    // Update progress bar and status
    progressBar.style.width = '10%';
    statusText.textContent = 'Checking Travian credentials...';
    
    // Get CSRF token
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || 
                     document.querySelector('input[name="csrf_token"]')?.value;
    
    console.log("CSRF Token found:", csrfToken ? "Yes" : "No");
    
    // Set up extraction process with indicators
    setTimeout(() => {
        progressBar.style.width = '30%';
        statusText.textContent = 'Logging into Travian...';
        
        setTimeout(() => {
            progressBar.style.width = '60%';
            statusText.textContent = 'Extracting village data...';
            
            // Send AJAX request to extract villages
            console.log("Sending extract villages request");
            fetch('/api/user/villages/extract', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': csrfToken || '',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({})
            })
            .then(response => {
                console.log("Response received:", response.status);
                return response.json();
            })
            .then(data => {
                console.log("Extract villages response:", data);
                progressBar.style.width = '100%';
                
                if (data.success) {
                    // Show success results
                    document.getElementById('extractProgress').classList.add('d-none');
                    document.getElementById('extractResults').classList.remove('d-none');
                    
                    // Update success message
                    document.getElementById('extractSuccessMessage').textContent = 
                        `Successfully extracted ${data.data.length} villages.`;
                    
                    // Populate villages list
                    const villagesList = document.getElementById('extractedVillagesList');
                    if (villagesList) {
                        villagesList.innerHTML = '';
                        
                        data.data.forEach(village => {
                            const listItem = document.createElement('li');
                            listItem.className = 'list-group-item';
                            listItem.textContent = `${village.name} (${village.x}|${village.y})`;
                            villagesList.appendChild(listItem);
                        });
                    }
                    
                    // Show Done button
                    document.getElementById('extractDoneBtn')?.classList.remove('d-none');
                    
                    // Refresh the page data after delay
                    setTimeout(() => {
                        window.location.reload();
                    }, 3000);
                } else {
                    // Show error
                    showExtractionError(data.message || 'Failed to extract villages');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showExtractionError('An error occurred while extracting villages');
            });
        }, 1500);
    }, 1000);
}

/**
 * Show extraction error
 * @param {string} message - Error message to display
 */
function showExtractionError(message) {
    console.error("Extraction error:", message);
    
    const extractError = document.getElementById('extractError');
    const extractErrorMessage = document.getElementById('extractErrorMessage');
    const extractProgress = document.getElementById('extractProgress');
    const extractCancelBtn = document.getElementById('extractCancelBtn');
    
    if (extractError && extractErrorMessage && extractProgress) {
        extractProgress.classList.add('d-none');
        extractError.classList.remove('d-none');
        extractErrorMessage.textContent = message;
        
        if (extractCancelBtn) {
            extractCancelBtn.classList.remove('d-none');
        }
    } else {
        console.error("Error elements not found in DOM");
        alert("Error: " + message);
    }
}