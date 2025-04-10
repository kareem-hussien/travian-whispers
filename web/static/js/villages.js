/**
 * Villages Management JavaScript
 * This file handles the villages extraction and management functionality for Travian Whispers.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Get the extract villages button
    const extractBtn = document.getElementById('extractVillages');
    
    // Get the refresh villages button
    const refreshBtn = document.getElementById('refreshVillages');
    
    // If extract button exists, add click event
    if (extractBtn) {
        extractBtn.addEventListener('click', showExtractModal);
    }
    
    // If refresh button exists, add click event
    if (refreshBtn) {
        refreshBtn.addEventListener('click', refreshVillagesList);
    }
    
    // Add event listeners to village actions
    attachVillageActionListeners();
});

/**
 * Shows the extraction modal and prepares extraction process
 */
function showExtractModal() {
    // Reset modal state
    document.getElementById('extractProgress').classList.remove('d-none');
    document.getElementById('extractResults').classList.add('d-none');
    document.getElementById('extractError').classList.add('d-none');
    
    document.getElementById('confirmExtractBtn').classList.remove('d-none');
    document.getElementById('extractCancelBtn').classList.remove('d-none');
    document.getElementById('extractDoneBtn').classList.add('d-none');
    
    // Show the modal
    const modal = new bootstrap.Modal(document.getElementById('extractVillagesModal'));
    modal.show();
}

/**
 * Starts the village extraction process via API
 */
function startVillageExtraction() {
    // Show progress section and hide others
    document.getElementById('extractProgress').classList.remove('d-none');
    document.getElementById('extractResults').classList.add('d-none');
    document.getElementById('extractError').classList.add('d-none');
    
    // Hide/show buttons
    document.getElementById('confirmExtractBtn').classList.add('d-none');
    document.getElementById('extractCancelBtn').classList.add('d-none');
    document.getElementById('extractDoneBtn').classList.add('d-none');
    
    // Update progress bar and status
    const progressBar = document.querySelector('#extractProgress .progress-bar');
    const statusText = document.getElementById('extractStatus');
    progressBar.style.width = '10%';
    statusText.textContent = 'Checking Travian credentials...';
    
    // Send AJAX request to extract villages with progress updates
    setTimeout(() => {
        progressBar.style.width = '30%';
        statusText.textContent = 'Logging into Travian...';
        
        setTimeout(() => {
            progressBar.style.width = '60%';
            statusText.textContent = 'Extracting village data...';
            
            // Get CSRF token
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
            
            // Send AJAX request to extract villages
            fetch('/api/user/villages/extract', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': csrfToken
                }
            })
            .then(response => response.json())
            .then(data => {
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
                    villagesList.innerHTML = '';
                    
                    data.data.forEach(village => {
                        const listItem = document.createElement('li');
                        listItem.className = 'list-group-item';
                        listItem.textContent = `${village.name} (${village.x}|${village.y})`;
                        villagesList.appendChild(listItem);
                    });
                    
                    // Show Done button
                    document.getElementById('extractDoneBtn').classList.remove('d-none');
                    
                    // Refresh the page data
                    refreshVillagesList();
                } else {
                    // Show error
                    showExtractionError(data.message || 'Failed to extract villages');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showExtractionError('An error occurred while extracting villages');
            });
        }, 1000);
    }, 800);
}

/**
 * Display extraction error in the modal
 * @param {string} message - Error message to display
 */
function showExtractionError(message) {
    document.getElementById('extractProgress').classList.add('d-none');
    document.getElementById('extractError').classList.remove('d-none');
    document.getElementById('extractErrorMessage').textContent = message;
    document.getElementById('extractCancelBtn').classList.remove('d-none');
}

/**
 * Refresh the villages list without reloading the page
 */
function refreshVillagesList() {
    // Show loading indicator on the button
    const refreshButton = document.getElementById('refreshVillages');
    if (refreshButton) {
        const originalText = refreshButton.innerHTML;
        refreshButton.disabled = true;
        refreshButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Refreshing...';
        
        // Get CSRF token
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
        
        // Fetch updated villages data
        fetch('/api/user/villages/list', {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRF-Token': csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update the villages table
                updateVillagesTable(data.data);
                
                // Update the hidden data field
                document.getElementById('villagesData').value = JSON.stringify(data.data);
                
                // Update the global variable
                window.villagesData = data.data;
                
                // Update settings dropdowns
                updateSettingsDropdowns(data.data);
                
                // Show success message
                showToast('Villages data refreshed successfully', 'success');
            } else {
                // Show error message
                showToast(data.message || 'Failed to refresh villages data', 'error');
            }
        })
        .catch(error => {
            console.error('Error refreshing villages data:', error);
            showToast('An error occurred while refreshing data', 'error');
        })
        .finally(() => {
            // Restore button state
            refreshButton.disabled = false;
            refreshButton.innerHTML = originalText;
        });
    }
}

/**
 * Update the villages table with new data
 * @param {Array} villages - Array of village objects
 */
function updateVillagesTable(villages) {
    const tableBody = document.querySelector('table tbody');
    if (!tableBody || !villages) return;
    
    // Clear existing rows
    tableBody.innerHTML = '';
    
    if (villages.length === 0) {
        // Show empty state
        const emptyRow = document.createElement('tr');
        emptyRow.innerHTML = `
            <td colspan="5" class="text-center py-4">
                <div class="alert alert-info mb-0">
                    <i class="bi bi-info-circle-fill me-2"></i>
                    No villages found. Click the "Extract Villages" button to fetch your villages from Travian.
                </div>
            </td>
        `;
        tableBody.appendChild(emptyRow);
        return;
    }
    
    // Add new rows
    villages.forEach(village => {
        const row = document.createElement('tr');
        
        // Format status badge
        const statusBadge = village.status === 'active' 
            ? '<span class="badge bg-success">Active</span>'
            : '<span class="badge bg-secondary">Inactive</span>';
        
        row.innerHTML = `
            <td>
                <div class="d-flex align-items-center">
                    <img src="/static/img/icon/village-icon.png" 
                         alt="Village" width="24" height="24" class="me-2">
                    <span>${village.name}</span>
                </div>
            </td>
            <td>(${village.x}|${village.y})</td>
            <td>${village.population || 'Unknown'}</td>
            <td>${statusBadge}</td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button type="button" class="btn btn-outline-primary village-details" 
                            data-village-id="${village.newdid}" data-bs-toggle="modal" 
                            data-bs-target="#villageDetailsModal">
                        <i class="bi bi-eye"></i>
                    </button>
                    <button type="button" class="btn btn-outline-warning village-edit" 
                            data-village-id="${village.newdid}" data-bs-toggle="modal" 
                            data-bs-target="#editVillageModal">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button type="button" class="btn btn-outline-danger village-remove" 
                            data-village-id="${village.newdid}" data-village-name="${village.name}">
                        <i class="bi bi-x-circle"></i>
                    </button>
                </div>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
    
    // Re-attach event listeners
    attachVillageActionListeners();
}

/**
 * Update settings dropdowns with current village data
 * @param {Array} villages - Array of village objects
 */
function updateSettingsDropdowns(villages) {
    const autoFarmSelect = document.getElementById('autoFarmVillages');
    const trainingSelect = document.getElementById('trainingVillages');
    
    if (!autoFarmSelect || !trainingSelect) return;
    
    // Clear existing options
    autoFarmSelect.innerHTML = '';
    trainingSelect.innerHTML = '';
    
    // Add new options
    villages.forEach(village => {
        // Auto-farm dropdown
        const autoFarmOption = document.createElement('option');
        autoFarmOption.value = village.newdid;
        autoFarmOption.textContent = `${village.name} (${village.x}|${village.y})`;
        autoFarmOption.selected = village.auto_farm_enabled;
        autoFarmSelect.appendChild(autoFarmOption);
        
        // Training dropdown
        const trainingOption = document.createElement('option');
        trainingOption.value = village.newdid;
        trainingOption.textContent = `${village.name} (${village.x}|${village.y})`;
        trainingOption.selected = village.training_enabled;
        trainingSelect.appendChild(trainingOption);
    });
}

/**
 * Show detailed village information in modal
 * @param {string} villageId - Village ID to display
 */
function showVillageDetails(villageId) {
    // Get villages data
    const villages = window.villagesData || JSON.parse(document.getElementById('villagesData').value || '[]');
    const village = villages.find(v => v.newdid === villageId);
    
    if (village) {
        // Set modal data attribute for village ID
        document.querySelector('#villageDetailsModal').setAttribute('data-village-id', villageId);
        
        // Update modal with village data
        document.getElementById('detailsVillageName').textContent = village.name;
        document.getElementById('detailsVillageCoords').textContent = `(${village.x}|${village.y})`;
        document.getElementById('detailsVillagePopulation').textContent = village.population || 'Unknown';
        document.getElementById('detailsVillageId').textContent = village.newdid;
        
        // Update resources if available
        if (village.resources) {
            document.getElementById('detailsResourceWood').textContent = village.resources.wood || '0';
            document.getElementById('detailsResourceClay').textContent = village.resources.clay || '0';
            document.getElementById('detailsResourceIron').textContent = village.resources.iron || '0';
            document.getElementById('detailsResourceCrop').textContent = village.resources.crop || '0';
        }
        
        // Update automation settings
        document.getElementById('detailsAutoFarm').checked = village.auto_farm_enabled || false;
        document.getElementById('detailsTraining').checked = village.training_enabled || false;
        
        // Update activity info if available
        document.getElementById('detailsLastFarm').textContent = village.last_farmed || 'Never';
        document.getElementById('detailsLastTraining').textContent = village.last_trained || 'Never';
    }
}

/**
 * Populate edit village form with village data
 * @param {string} villageId - Village ID to edit
 */
function populateEditVillageForm(villageId) {
    const villages = window.villagesData || JSON.parse(document.getElementById('villagesData').value || '[]');
    const village = villages.find(v => v.newdid === villageId);
    
    if (village) {
        // Set form field values
        document.getElementById('editVillageId').value = village.newdid;
        document.getElementById('editVillageName').value = village.name;
        document.getElementById('editVillageX').value = village.x;
        document.getElementById('editVillageY').value = village.y;
        document.getElementById('editVillagePopulation').value = village.population || '';
        document.getElementById('editAutoFarm').checked = village.auto_farm_enabled || false;
        document.getElementById('editTraining').checked = village.training_enabled || false;
    }
}

/**
 * Show remove village confirmation
 * @param {string} villageId - Village ID to remove
 * @param {string} villageName - Village name
 */
function showRemoveVillageConfirmation(villageId, villageName) {
    document.getElementById('removeVillageId').value = villageId;
    document.getElementById('removeVillageName').textContent = villageName;
    const modal = new bootstrap.Modal(document.getElementById('removeVillageModal'));
    modal.show();
}

/**
 * Save village changes
 */
function saveVillageChanges() {
    const villageId = document.getElementById('editVillageId').value;
    const villageName = document.getElementById('editVillageName').value;
    const villageX = document.getElementById('editVillageX').value;
    const villageY = document.getElementById('editVillageY').value;
    const villagePopulation = document.getElementById('editVillagePopulation').value;
    const autoFarmEnabled = document.getElementById('editAutoFarm').checked;
    const trainingEnabled = document.getElementById('editTraining').checked;
    
    // Validate inputs
    if (!villageName) {
        showToast('Village name cannot be empty', 'error');
        return;
    }
    
    if (!villageX || !villageY) {
        showToast('Coordinates are required', 'error');
        return;
    }
    
    // Get villages data
    const villages = window.villagesData || JSON.parse(document.getElementById('villagesData').value || '[]');
    
    // Find and update the village
    const villageIndex = villages.findIndex(v => v.newdid === villageId);
    
    if (villageIndex === -1) {
        showToast('Village not found', 'error');
        return;
    }
    
    // Update village data
    villages[villageIndex].name = villageName;
    villages[villageIndex].x = parseInt(villageX);
    villages[villageIndex].y = parseInt(villageY);
    villages[villageIndex].population = parseInt(villagePopulation) || 0;
    villages[villageIndex].auto_farm_enabled = autoFarmEnabled;
    villages[villageIndex].training_enabled = trainingEnabled;
    
    // Get CSRF token
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    
    // Send AJAX request to update villages
    fetch('/api/user/villages/update', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrfToken
        },
        body: JSON.stringify({
            villages: villages
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('editVillageModal'));
            modal.hide();
            
            // Show success message
            showToast('Village updated successfully', 'success');
            
            // Refresh the page to show updated data
            refreshVillagesList();
        } else {
            // Show error message
            showToast(data.message || 'Error updating village', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('An error occurred while updating the village', 'error');
    });
}

/**
 * Remove village
 */
function removeVillage() {
    const villageId = document.getElementById('removeVillageId').value;
    
    // Get villages data
    const villages = window.villagesData || JSON.parse(document.getElementById('villagesData').value || '[]');
    
    // Remove the village
    const updatedVillages = villages.filter(v => v.newdid !== villageId);
    
    // Get CSRF token
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    
    // Send AJAX request to update villages
    fetch('/api/user/villages/update', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrfToken
        },
        body: JSON.stringify({
            villages: updatedVillages
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('removeVillageModal'));
            modal.hide();
            
            // Show success message
            showToast('Village removed successfully', 'success');
            
            // Refresh the page to show updated data
            refreshVillagesList();
        } else {
            // Show error message
            showToast(data.message || 'Error removing village', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('An error occurred while removing the village', 'error');
    });
}

/**
 * Save village settings
 */
function saveVillageSettings() {
    // Get selected villages for auto farm
    const autoFarmVillages = Array.from(document.getElementById('autoFarmVillages').selectedOptions).map(option => option.value);
    
    // Get selected villages for troop training
    const trainingVillages = Array.from(document.getElementById('trainingVillages').selectedOptions).map(option => option.value);
    
    // Get villages data
    const villages = window.villagesData || JSON.parse(document.getElementById('villagesData').value || '[]');
    
    // Update village settings
    villages.forEach(village => {
        village.auto_farm_enabled = autoFarmVillages.includes(village.newdid);
        village.training_enabled = trainingVillages.includes(village.newdid);
    });
    
    // Get CSRF token
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    
    // Send AJAX request to update villages
    fetch('/api/user/villages/update', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrfToken
        },
        body: JSON.stringify({
            villages: villages
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show success message
            showToast('Village settings saved successfully', 'success');
            
            // Refresh the villages data to reflect changes
            refreshVillagesList();
        } else {
            // Show error message
            showToast(data.message || 'Error saving village settings', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('An error occurred while saving village settings', 'error');
    });
}

/**
 * Attach event listeners to village action buttons
 */
function attachVillageActionListeners() {
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
}

/**
 * Shows a toast message
 * @param {string} message - Message to display
 * @param {string} type - Message type (success, error, warning, info)
 */
function showToast(message, type = 'info') {
    // Check if toast container exists, create it if not
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    // Set toast content
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    // Add to container
    toastContainer.appendChild(toast);
    
    // Initialize and show toast
    const toastInstance = new bootstrap.Toast(toast, {
        delay: 5000
    });
    toastInstance.show();
    
    // Remove from DOM after hiding
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

// Add event listeners when document is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Button handlers for extract villages modal
    document.getElementById('confirmExtractBtn')?.addEventListener('click', function() {
        startVillageExtraction();
    });
    
    // Button handlers for edit village modal
    document.getElementById('saveVillageBtn')?.addEventListener('click', function() {
        saveVillageChanges();
    });
    
    // Button handlers for remove village modal
    document.getElementById('confirmRemoveBtn')?.addEventListener('click', function() {
        removeVillage();
    });
    
    // Village settings form submit
    document.getElementById('villageSettingsForm')?.addEventListener('submit', function(e) {
        e.preventDefault();
        saveVillageSettings();
    });
});