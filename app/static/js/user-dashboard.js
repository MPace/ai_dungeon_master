/**
 * User Dashboard JavaScript
 * Handles interactions on the user dashboard page
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('User dashboard JS loaded');
    
    // Set up delete character buttons
    setupDeleteCharacterButtons();
    
    // Set up delete draft buttons
    setupDeleteDraftButtons();
});

/**
 * Set up event listeners for delete character buttons
 */
function setupDeleteCharacterButtons() {
    // Find all delete character links
    const deleteCharLinks = document.querySelectorAll('.delete-character-btn');
    
    deleteCharLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const characterId = this.getAttribute('data-character-id');
            const characterName = this.getAttribute('data-character-name');
            
            if (!characterId) {
                console.error('No character ID provided for deletion');
                return;
            }
            
            // Show confirmation dialog
            const confirmMessage = characterName ? 
                `Are you sure you want to delete "${characterName}"? This cannot be undone.` : 
                'Are you sure you want to delete this character? This cannot be undone.';
                
            if (confirm(confirmMessage)) {
                deleteCharacter(characterId);
            }
        });
    });
}

/**
 * Set up event listeners for delete draft buttons
 */
function setupDeleteDraftButtons() {
    // Find all delete draft links
    const deleteDraftLinks = document.querySelectorAll('.delete-draft-btn');
    
    deleteDraftLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const draftId = this.getAttribute('data-draft-id');
            const draftName = this.getAttribute('data-draft-name') || 'Unnamed draft';
            
            if (!draftId) {
                console.error('No draft ID provided for deletion');
                return;
            }
            
            // Show confirmation dialog
            if (confirm(`Are you sure you want to delete the draft "${draftName}"? This cannot be undone.`)) {
                deleteDraft(draftId);
            }
        });
    });
}

/**
 * Delete a character via API call
 * @param {string} characterId - The ID of the character to delete
 */
function deleteCharacter(characterId) {
    console.log(`Deleting character: ${characterId}`);
    
    // Show loading indicator on the page
    showLoadingIndicator();
    
    // Send delete request to the server
    fetch(`/character/api/delete-character/${characterId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || `Server returned ${response.status}`);
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('Delete response:', data);
        
        if (data.success) {
            // Show success message
            showAlert('success', data.message || 'Character deleted successfully');
            console.log(data.message);
        
            // Remove the character from the UI
            const characterRow = document.querySelector(`tr[data-character-id="${characterId}"]`);
            if (characterRow) {
                characterRow.remove();
                
                // Update the character count badge
                updateCharacterCounter();
            } else {
                // If we can't find the row, just reload the page
                window.location.reload();
            }
        } else {
            console.error(data.error);
            showAlert('danger', data.error || 'Failed to delete character');
        }
    })
    .catch(error => {
        console.error('Error deleting character:', error);
        showAlert('danger', `Error: ${error.message}`);
    })
    .finally(() => {
        hideLoadingIndicator();
    });
}

/**
 * Delete a draft via API call
 * @param {string} draftId - The ID of the draft to delete
 */
function deleteDraft(draftId) {
    console.log(`Deleting draft: ${draftId}`);
    
    // Show loading indicator on the page
    showLoadingIndicator();
    
    // Send delete request to the server
    fetch(`/character/api/delete-draft/${draftId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || `Server returned ${response.status}`);
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('Delete response:', data);
        
        if (data.success) {
            // Show success message
            console.log(data.message);
            showAlert('success', data.message || 'Draft deleted successfully');
    
            // Remove the draft from the UI
            const draftRow = document.querySelector(`tr[data-draft-id="${draftId}"]`);
            if (draftRow) {
                draftRow.remove();
                
                // Update the draft count badge
                updateDraftCounter();
            } else {
                // If we can't find the row, just reload the page
                window.location.reload();
            }
        } else {
            console.error('Error:', error);
            showAlert('danger', data.error || 'Failed to delete draft');
        }
    })
    .catch(error => {
        console.error('Error deleting draft:', error);
        showAlert('danger', `Error: ${error.message}`);
    })
    .finally(() => {
        hideLoadingIndicator();
    });
}

/**
 * Update the character counter badge
 */
function updateCharacterCounter() {
    const characterList = document.querySelector('table.characters-table tbody');
    const counterBadge = document.querySelector('.card-header .badge[data-counter="characters"]');
    
    if (characterList && counterBadge) {
        const characterCount = characterList.querySelectorAll('tr').length;
        counterBadge.textContent = characterCount;
        
        // If no characters left, show the empty message
        if (characterCount === 0) {
            const tableBody = characterList.closest('.table-responsive');
            if (tableBody) {
                tableBody.innerHTML = `
                    <div class="p-4 text-center">
                        <p class="mb-0">You haven't created any characters yet.</p>
                    </div>
                `;
            }
        }
    }
}

/**
 * Update the draft counter badge
 */
function updateDraftCounter() {
    const draftList = document.querySelector('table.drafts-table tbody');
    const counterBadge = document.querySelector('.card-header .badge[data-counter="drafts"]');
    
    if (draftList && counterBadge) {
        const draftCount = draftList.querySelectorAll('tr').length;
        counterBadge.textContent = draftCount;
        
        // If no drafts left, hide the drafts section
        if (draftCount === 0) {
            const draftsCard = draftList.closest('.card');
            if (draftsCard) {
                draftsCard.closest('.row').style.display = 'none';
            }
        }
    }
}

/**
 * Show a loading indicator on the page
 */
function showLoadingIndicator() {
    // Check if loading indicator already exists
    if (document.querySelector('.loading-overlay')) {
        return;
    }
    
    // Create loading overlay
    const loadingOverlay = document.createElement('div');
    loadingOverlay.className = 'loading-overlay';
    loadingOverlay.innerHTML = `
        <div class="spinner-border text-light" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
    `;
    
    // Add to body
    document.body.appendChild(loadingOverlay);
    
    // Add a small delay to ensure the overlay is fully visible
    setTimeout(() => {
        loadingOverlay.style.opacity = '1';
    }, 10);
}

/**
 * Hide the loading indicator
 */
function hideLoadingIndicator() {
    const loadingOverlay = document.querySelector('.loading-overlay');
    if (loadingOverlay) {
        // Fade out
        loadingOverlay.style.opacity = '0';
        
        // Remove after animation
        setTimeout(() => {
            if (document.body.contains(loadingOverlay)) {
                document.body.removeChild(loadingOverlay);
            }
        }, 300);
    }
}

/**
 * Show an alert message at the top of the page
 * @param {string} type - Alert type: success, danger, warning, info
 * @param {string} message - The message to display
 */
function showAlert(type, message) {
    // Create container if it doesn't exist
    let alertContainer = document.querySelector('.alert-container');
    if (!alertContainer) {
        alertContainer = document.createElement('div');
        alertContainer.className = 'alert-container';
        
        // Insert after header
        const header = document.querySelector('header');
        if (header && header.nextSibling) {
            header.parentNode.insertBefore(alertContainer, header.nextSibling);
        } else {
            // Fallback to beginning of container
            const container = document.querySelector('.container-fluid');
            if (container && container.firstChild) {
                container.insertBefore(alertContainer, container.firstChild);
            } else {
                document.body.prepend(alertContainer);
            }
        }
    }
    
    // Create alert
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.role = 'alert';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add to container
    alertContainer.appendChild(alert);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alert && alertContainer.contains(alert)) {
            alert.classList.remove('show');
            setTimeout(() => {
                if (alert && alertContainer.contains(alert)) {
                    alertContainer.removeChild(alert);
                }
            }, 150);
        }
    }, 5000);
}