/**
 * Travian Whispers - Admin Settings Panel
 * This file handles the interactive functionality of the admin settings page
 */

/**
 * Show a specific settings section and hide the cards view
 * @param {string} settingsName - The name of the settings section to show
 */
function showSettings(settingsName) {
    // Hide all settings content
    document.querySelectorAll('.settings-content').forEach(content => {
        content.classList.remove('active');
    });
    
    // Hide cards
    document.getElementById('settings-cards').style.display = 'none';
    
    // Show the selected settings content
    const settingsContent = document.getElementById(`${settingsName}-settings`);
    if (settingsContent) {
        settingsContent.classList.add('active');
        
        // Save the active section to localStorage
        localStorage.setItem('activeSettingsSection', settingsName);
        
        // Update URL if needed (without refreshing the page)
        const url = new URL(window.location.href);
        url.searchParams.set('tab', settingsName);
        window.history.replaceState({}, '', url);
    }
}

/**
 * Hide a specific settings section and show the cards view
 * @param {string} settingsName - The name of the settings section to hide
 */
function hideSettings(settingsName) {
    // Hide the settings content
    const settingsContent = document.getElementById(`${settingsName}-settings`);
    if (settingsContent) {
        settingsContent.classList.remove('active');
    }
    
    // Show cards
    document.getElementById('settings-cards').style.display = 'grid';
    
    // Remove the tab parameter from URL
    const url = new URL(window.location.href);
    url.searchParams.delete('tab');
    window.history.replaceState({}, '', url);
    
    // Remove from localStorage
    localStorage.removeItem('activeSettingsSection');
}

/**
 * Initialize settings page functionality
 */
document.addEventListener('DOMContentLoaded', function() {
    // Get the active tab from the URL or localStorage
    const urlParams = new URLSearchParams(window.location.search);
    const tabParam = urlParams.get('tab');
    
    if (tabParam) {
        showSettings(tabParam);
    } else {
        // Check if there's a saved setting in localStorage
        const savedSetting = localStorage.getItem('activeSettingsSection');
        if (savedSetting) {
            showSettings(savedSetting);
        }
    }
    
    // Handle form submission to preserve tab selection
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            // Find the active settings content
            const activeSettings = document.querySelector('.settings-content.active');
            if (activeSettings) {
                const settingsName = activeSettings.getAttribute('data-settings-name');
                
                // Add a hidden field to store the active tab
                let tabInput = document.createElement('input');
                tabInput.type = 'hidden';
                tabInput.name = 'active_tab';
                tabInput.value = settingsName;
                
                this.appendChild(tabInput);
            }
        });
    });
    
    // Make entire card clickable
    document.querySelectorAll('.settings-card').forEach(card => {
        card.addEventListener('click', function() {
            const settingsTarget = this.getAttribute('data-settings-target');
            if (settingsTarget) {
                showSettings(settingsTarget);
            }
        });
    });
});
