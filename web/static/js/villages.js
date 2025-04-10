/**
 * Travian Whispers - Villages Management JavaScript
 * This file handles all the frontend interactions for the villages page
 */

document.addEventListener('DOMContentLoaded', function() {
    // Debug initialization - Add more detailed logging
    console.log("Villages.js loaded and initialized");
    
    // Log DOM elements to verify they exist
    console.log("Extract Villages button:", document.getElementById('extractVillages'));
    console.log("Extract Villages Modal:", document.getElementById('extractVillagesModal'));
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Extract Villages button - FIX: Add more robust selector and error handling
    const extractVillagesBtn = document.getElementById('extractVillages');
    if (extractVillagesBtn) {
        console.log("Extract Villages button found");
        extractVillagesBtn.addEventListener('click', function(event) {
            event.preventDefault(); // Prevent any default action
            console.log("Extract Villages button clicked");
            showExtractModal();
        });
    } else {
        console.error("Extract Villages button not found! Trying alternative selector...");
        // Try alternative selector
        const altButtons = document.querySelectorAll('button[data-bs-toggle="modal"][data-bs-target="#extractVillagesModal"]');
        if (altButtons.length > 0) {
            console.log("Found alternative button via selector");
            altButtons[0].addEventListener('click', function(event) {
                event.preventDefault();
                console.log("Alternative extract button clicked");
                showExtractModal();
            });
        } else {
            console.error("No extract button found on page!");
        }
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
    
    // Save village edit - FIX: Add null check with ? operator
    document.getElementById('saveVillageBtn')?.addEventListener('click', function() {
        saveVillageChanges();
    });
    
    // Add village button - FIX: Add null check with ? operator
    document.getElementById('addVillageBtn')?.addEventListener('click', function() {
        addVillage();
    });
    
    // Confirm remove village button - FIX: Add null check with ? operator
    document.getElementById('confirmRemoveBtn')?.addEventListener('click', function() {
        removeVillage();
    });
    
    // Village settings form submit - FIX: Add null check with ? operator
    document.getElementById('villageSettingsForm')?.addEventListener('submit', function(e) {
        e.preventDefault();
        saveVillageSettings();
    });
    
    // Confirm extract villages button - FIX: Add more robust error handling
    const confirmExtractBtn = document.getElementById('confirmExtractBtn');
    if (confirmExtractBtn) {
        console.log("Confirm Extract button found");
        confirmExtractBtn.addEventListener('click', function() {
            console.log("Confirm Extract button clicked");
            startVillageExtraction();
        });
    } else {
        console.error("Confirm Extract button not found! Check modal HTML.");
    }
    
    // Refresh villages button - FIX: Add null check with ? operator
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
        alert("Error: Extract Villages modal not found. Please contact support.");
        return;
    }
    
    // Reset the modal state
    const progressElement = document.getElementById('extractProgress');
    const resultsElement = document.getElementById('extractResults');
    const errorElement = document.getElementById('extractError');
    
    if (progressElement) progressElement.classList.add('d-none');
    if (resultsElement) resultsElement.classList.add('d-none');
    if (errorElement) errorElement.classList.add('d-none');
    
    const confirmBtn = document.getElementById('confirmExtractBtn');
    const cancelBtn = document.getElementById('extractCancelBtn');
    const doneBtn = document.getElementById('extractDoneBtn');
    
    if (confirmBtn) confirmBtn.classList.remove('d-none');
    if (cancelBtn) cancelBtn.classList.remove('d-none');
    if (doneBtn) doneBtn.classList.add('d-none');
    
    // Check if Bootstrap is available
    if (typeof bootstrap === 'undefined') {
        console.error("Bootstrap not found! Modal cannot be displayed.");
        alert("Error: Bootstrap library not loaded. Please refresh the page.");
        return;
    }
    
    // Show the modal
    try {
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
        console.log("Modal shown successfully");
    } catch (error) {
        console.error("Error showing modal:", error);
        alert("Error showing the extraction modal. Please try again or refresh the page.");
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
        alert("Error: Unable to start extraction. Missing UI elements.");
        return;
    }
    
    // Show progress section and hide others
    progressElement.classList.remove('d-none');
    
    const resultsElement = document.getElementById('extractResults');
    const errorElement = document.getElementById('extractError');
    
    if (resultsElement) resultsElement.classList.add('d-none');
    if (errorElement) errorElement.classList.add('d-none');
    
    // Hide/show buttons
    const confirmBtn = document.getElementById('confirmExtractBtn');
    const cancelBtn = document.getElementById('extractCancelBtn');
    const doneBtn = document.getElementById('extractDoneBtn');
    
    if (confirmBtn) confirmBtn.classList.add('d-none');
    if (cancelBtn) cancelBtn.classList.add('d-none');
    if (doneBtn) doneBtn.classList.add('d-none');
    
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
                    'Accept': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({})
            })
            .then(response => {
                console.log("Response received:", response.status);
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log("Extract villages response:", data);
                progressBar.style.width = '100%';
                
                if (data.success) {
                    // Show success results
                    if (progressElement) progressElement.classList.add('d-none');
                    if (resultsElement) resultsElement.classList.remove('d-none');
                    
                    // Update success message
                    const extractSuccessMessage = document.getElementById('extractSuccessMessage');
                    if (extractSuccessMessage) {
                        extractSuccessMessage.textContent = 
                            `Successfully extracted ${data.data.length} villages.`;
                    }
                    
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
                    if (doneBtn) doneBtn.classList.remove('d-none');
                    
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
                console.error('Extraction error:', error);
                showExtractionError(`Error: ${error.message || 'Unknown error occurred'}`);
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

/**
 * These functions are placeholders but need to be defined to prevent errors
 * when they're called from event listeners
 */

function showVillageDetails(villageId) {
    console.log("Show village details for:", villageId);
    // Implementation would be added based on actual requirements
}

function populateEditVillageForm(villageId) {
    console.log("Edit village:", villageId);
    // Implementation would be added based on actual requirements
}

function showRemoveVillageConfirmation(villageId, villageName) {
    console.log("Remove village confirmation:", villageId, villageName);
    
    // Find and update the modal elements
    const removeVillageName = document.getElementById('removeVillageName');
    const removeVillageId = document.getElementById('removeVillageId');
    
    if (removeVillageName) removeVillageName.textContent = villageName;
    if (removeVillageId) removeVillageId.value = villageId;
    
    // Show the modal
    const modal = document.getElementById('removeVillageModal');
    if (modal && typeof bootstrap !== 'undefined') {
        new bootstrap.Modal(modal).show();
    }
}

function saveVillageChanges() {
    console.log("Save village changes");
    // Implementation would be added based on actual requirements
}

function addVillage() {
    console.log("Add village");
    // Implementation would be added based on actual requirements
}

function removeVillage() {
    console.log("Remove village");
    const villageId = document.getElementById('removeVillageId')?.value;
    
    if (!villageId) {
        console.error("No village ID found for removal");
        return;
    }
    
    console.log("Removing village:", villageId);
    
    // Get CSRF token
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || 
                    document.querySelector('input[name="csrf_token"]')?.value;
    
    // Send removal request
    fetch('/api/user/villages/remove', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrfToken || '',
            'Accept': 'application/json'
        },
        body: JSON.stringify({
            village_id: villageId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Close modal if it exists
            const modal = bootstrap.Modal.getInstance(document.getElementById('removeVillageModal'));
            if (modal) modal.hide();
            
            // Show success message
            alert("Village removed successfully");
            
            // Reload page to update villages list
            window.location.reload();
        } else {
            alert("Error: " + (data.message || "Failed to remove village"));
        }
    })
    .catch(error => {
        console.error("Error removing village:", error);
        alert("Error removing village. Please try again.");
    });
}

function saveVillageSettings() {
    console.log("Save village settings");
    
    // Get selected villages
    const autoFarmVillages = Array.from(document.getElementById('autoFarmVillages')?.selectedOptions || [])
        .map(option => option.value);
    
    const trainingVillages = Array.from(document.getElementById('trainingVillages')?.selectedOptions || [])
        .map(option => option.value);
    
    console.log("Auto Farm Villages:", autoFarmVillages);
    console.log("Training Villages:", trainingVillages);
    
    // Get CSRF token
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || 
                    document.querySelector('input[name="csrf_token"]')?.value;
    
    // Send settings update request
    fetch('/api/user/villages/settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrfToken || '',
            'Accept': 'application/json'
        },
        body: JSON.stringify({
            auto_farm_villages: autoFarmVillages,
            training_villages: trainingVillages
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("Village settings updated successfully");
        } else {
            alert("Error: " + (data.message || "Failed to update village settings"));
        }
    })
    .catch(error => {
        console.error("Error saving village settings:", error);
        alert("Error saving settings. Please try again.");
    });
}

function refreshVillagesData() {
    console.log("Refresh villages data");
    window.location.reload();
}
