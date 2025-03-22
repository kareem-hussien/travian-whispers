document.addEventListener('DOMContentLoaded', function() {
    // Check if we need to show a specific settings section from URL hash or query param
    const urlParams = new URLSearchParams(window.location.search);
    const tabParam = urlParams.get('tab');
    if (tabParam) {
        showSettings(tabParam);
    } else if (window.location.hash) {
        const hash = window.location.hash.substring(1);
        showSettings(hash);
    }

    // Add click handlers to all settings cards
    const settingsCards = document.querySelectorAll('.settings-card');
    settingsCards.forEach(card => {
        card.addEventListener('click', function() {
            const target = this.getAttribute('data-settings-target');
            showSettings(target);
        });
    });

    // Handle back buttons
    const backButtons = document.querySelectorAll('.back-to-cards');
    backButtons.forEach(button => {
        button.addEventListener('click', function() {
            hideAllSettings();
            showSettingsCards();
        });
    });
});

// Show a specific settings section
function showSettings(settingsName) {
    // Hide all settings sections first
    hideAllSettings();
    
    // Hide settings cards
    hideSettingsCards();
    
    // Show the requested settings section
    const settingsSection = document.querySelector(`.settings-content[data-settings-name="${settingsName}"]`);
    if (settingsSection) {
        settingsSection.classList.add('active');
        // Update URL hash for bookmarking
        window.location.hash = settingsName;
        
        // Add active tab to form if it exists
        const forms = settingsSection.querySelectorAll('form');
        forms.forEach(form => {
            // Create or update hidden input for active tab
            let activeTabInput = form.querySelector('input[name="active_tab"]');
            if (!activeTabInput) {
                activeTabInput = document.createElement('input');
                activeTabInput.type = 'hidden';
                activeTabInput.name = 'active_tab';
                form.appendChild(activeTabInput);
            }
            activeTabInput.value = settingsName;
        });
    } else {
        // If section not found, show cards
        showSettingsCards();
    }
}

// Hide all settings sections
function hideAllSettings() {
    const allSettings = document.querySelectorAll('.settings-content');
    allSettings.forEach(section => {
        section.classList.remove('active');
    });
}

// Hide settings cards view
function hideSettingsCards() {
    const cardsContainer = document.getElementById('settings-cards');
    if (cardsContainer) {
        cardsContainer.classList.add('hidden');
    }
}

// Show settings cards view
function showSettingsCards() {
    const cardsContainer = document.getElementById('settings-cards');
    if (cardsContainer) {
        cardsContainer.classList.remove('hidden');
    }
    // Clear URL hash
    history.replaceState(null, null, ' ');
}

// Function that can be called from HTML onclick
function hideSettings(settingsName) {
    hideAllSettings();
    showSettingsCards();
}
