/**
 * Memory Management UI
 * 
 * This module handles the UI for interacting with the memory system
 */

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Memory Management UI loaded');
    
    // Initialize memory management UI
    initMemoryManagementUI();
});

// Global state
let currentSessionId = null;
let pinnedMemories = [];
let sessionEntities = {};

/**
 * Initialize memory management UI
 */
function initMemoryManagementUI() {
    // Create memory panel if it doesn't exist
    createMemoryPanel();
    
    // Setup event listeners for memory actions
    setupMemoryControls();
    
    // Get session ID from URL param or data attribute
    const urlParams = new URLSearchParams(window.location.search);
    currentSessionId = urlParams.get('session_id') || 
                      document.getElementById('chatWindow')?.getAttribute('data-session-id');
    
    // Load memory data if we have a session ID
    if (currentSessionId) {
        console.log('Loading memory data for session:', currentSessionId);
        loadSessionMemories();
        loadSessionEntities();
    } else {
        console.log('No session ID found, memory features will be available after the first message');
    }
    
    // Modify sendMessage function to capture session ID from response
    patchSendMessageFunction();
}

/**
 * Create the memory management panel in the UI
 */
function createMemoryPanel() {
    // Check if the memory panel already exists
    if (document.getElementById('memoryManagementPanel')) {
        return;
    }
    
    // Find the sidebar column
    const sidebar = document.querySelector('.sidebar-column');
    if (!sidebar) {
        console.error('Sidebar column not found');
        return;
    }
    
    // Create memory panel HTML
    const memoryPanel = document.createElement('div');
    memoryPanel.id = 'memoryManagementPanel';
    memoryPanel.classList.add('card', 'shadow', 'mb-4', 'border-0');
    memoryPanel.innerHTML = `
        <div class="card-header bg-dark text-light border-bottom border-secondary d-flex justify-content-between align-items-center">
            <h5 class="mb-0"><i class="bi bi-braces me-2"></i>Campaign Memory</h5>
            <button class="btn btn-sm btn-outline-light" id="refreshMemoriesBtn" title="Refresh">
                <i class="bi bi-arrow-clockwise"></i>
            </button>
        </div>
        <div class="card-body p-0">
            <!-- Memory Tabs -->
            <ul class="nav nav-tabs" id="memoryTabs" role="tablist">
                <li class="nav-item" role="presentation">
                    <button class="nav-link active" id="entities-tab" data-bs-toggle="tab" data-bs-target="#entities-tab-pane" 
                            type="button" role="tab" aria-controls="entities-tab-pane" aria-selected="true">
                        <i class="bi bi-people me-1"></i>Entities
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="memories-tab" data-bs-toggle="tab" data-bs-target="#memories-tab-pane" 
                            type="button" role="tab" aria-controls="memories-tab-pane" aria-selected="false">
                        <i class="bi bi-bookmark me-1"></i>Pinned
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="summary-tab" data-bs-toggle="tab" data-bs-target="#summary-tab-pane" 
                            type="button" role="tab" aria-controls="summary-tab-pane" aria-selected="false">
                        <i class="bi bi-journal-text me-1"></i>Summary
                    </button>
                </li>
            </ul>
            
            <!-- Tab content -->
            <div class="tab-content" id="memoryTabsContent">
                <!-- Entities tab -->
                <div class="tab-pane fade show active" id="entities-tab-pane" role="tabpanel" aria-labelledby="entities-tab" tabindex="0">
                    <div class="p-2">
                        <div class="entities-filter mb-2">
                            <div class="btn-group btn-group-sm w-100">
                                <button type="button" class="btn btn-outline-secondary active" data-filter="all">All</button>
                                <button type="button" class="btn btn-outline-secondary" data-filter="npc">NPCs</button>
                                <button type="button" class="btn btn-outline-secondary" data-filter="location">Places</button>
                                <button type="button" class="btn btn-outline-secondary" data-filter="item">Items</button>
                            </div>
                        </div>
                        <div id="entitiesList" class="list-group list-group-flush" style="max-height: 300px; overflow-y: auto;">
                            <div class="text-center p-3 text-muted">
                                <i class="bi bi-hourglass me-2"></i>Loading entities...
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Pinned memories tab -->
                <div class="tab-pane fade" id="memories-tab-pane" role="tabpanel" aria-labelledby="memories-tab" tabindex="0">
                    <div class="p-2">
                        <div id="pinnedMemoriesList" class="list-group list-group-flush" style="max-height: 300px; overflow-y: auto;">
                            <div class="text-center p-3 text-muted">
                                <i class="bi bi-hourglass me-2"></i>Loading pinned memories...
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Summary tab -->
                <div class="tab-pane fade" id="summary-tab-pane" role="tabpanel" aria-labelledby="summary-tab" tabindex="0">
                    <div class="p-2">
                        <div id="sessionSummary" class="p-3 bg-dark text-light rounded" style="max-height: 300px; overflow-y: auto;">
                            <div class="text-center text-muted">
                                <i class="bi bi-hourglass me-2"></i>Loading session summary...
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Insert the panel before the character sheet
    const characterSheet = sidebar.querySelector('.character-card');
    if (characterSheet) {
        sidebar.insertBefore(memoryPanel, characterSheet);
    } else {
        sidebar.appendChild(memoryPanel);
    }
}

/**
 * Set up event listeners for memory controls
 */
function setupMemoryControls() {
    // Refresh button
    document.getElementById('refreshMemoriesBtn')?.addEventListener('click', function() {
        if (currentSessionId) {
            loadSessionMemories();
            loadSessionEntities();
            loadSessionSummary();
        } else {
            alert('No active session found. Start a conversation first.');
        }
    });
    
    // Entity filter buttons
    document.querySelectorAll('.entities-filter button').forEach(button => {
        button.addEventListener('click', function() {
            // Update active state
            document.querySelectorAll('.entities-filter button').forEach(btn => {
                btn.classList.remove('active');
            });
            this.classList.add('active');
            
            // Apply filter
            const filterType = this.getAttribute('data-filter');
            filterEntities(filterType);
        });
    });
    
    // Memory tabs event
    document.querySelectorAll('#memoryTabs button').forEach(button => {
        button.addEventListener('click', function(event) {
            const tabId = this.getAttribute('id');
            
            // Load data if needed
            if (tabId === 'memories-tab' && pinnedMemories.length === 0) {
                loadPinnedMemories();
            } else if (tabId === 'summary-tab') {
                loadSessionSummary();
            }
        });
    });
}

/**
 * Load session memories
 */
function loadSessionMemories() {
    if (!currentSessionId) {
        console.error('No session ID for loading memories');
        return;
    }
    
    // Get CSRF token from meta tag
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    
    // Fetch memories from API
    fetch(`/api/memories/${currentSessionId}?limit=100&type=all`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            console.log('Loaded session memories:', data.memories.length);
            // Process memories
            processMemories(data.memories);
        } else {
            console.error('Error loading memories:', data.error);
            document.getElementById('pinnedMemoriesList').innerHTML = `
                <div class="text-center p-3 text-muted">
                    <i class="bi bi-exclamation-triangle me-2"></i>${data.error || 'Failed to load memories'}
                </div>
            `;
        }
    })
    .catch(error => {
        console.error('Error fetching memories:', error);
        document.getElementById('pinnedMemoriesList').innerHTML = `
            <div class="text-center p-3 text-muted">
                <i class="bi bi-exclamation-triangle me-2"></i>Error loading memories
            </div>
        `;
    });
}

/**
 * Load session entities
 */
function loadSessionEntities() {
    if (!currentSessionId) {
        console.error('No session ID for loading entities');
        return;
    }
    
    // Get CSRF token from meta tag
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    
    // Fetch entities from API
    fetch(`/api/entities/${currentSessionId}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            console.log('Loaded session entities:', Object.keys(data.entities).length);
            // Save entities to state
            sessionEntities = data.entities;
            // Render entities
            renderEntities(data.entities);
        } else {
            console.error('Error loading entities:', data.error);
            document.getElementById('entitiesList').innerHTML = `
                <div class="text-center p-3 text-muted">
                    <i class="bi bi-exclamation-triangle me-2"></i>${data.error || 'Failed to load entities'}
                </div>
            `;
        }
    })
    .catch(error => {
        console.error('Error fetching entities:', error);
        document.getElementById('entitiesList').innerHTML = `
            <div class="text-center p-3 text-muted">
                <i class="bi bi-exclamation-triangle me-2"></i>Error loading entities
            </div>
        `;
    });
}

/**
 * Load pinned memories
 */
function loadPinnedMemories() {
    if (!currentSessionId) {
        console.error('No session ID for loading pinned memories');
        return;
    }
    
    // Get CSRF token from meta tag
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    
    // Fetch pinned memories from API
    fetch(`/api/memories/${currentSessionId}?type=pinned`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            console.log('Loaded pinned memories:', data.memories.length);
            // Save pinned memories to state
            pinnedMemories = data.memories;
            // Render pinned memories
            renderPinnedMemories(data.memories);
        } else {
            console.error('Error loading pinned memories:', data.error);
            document.getElementById('pinnedMemoriesList').innerHTML = `
                <div class="text-center p-3 text-muted">
                    <i class="bi bi-exclamation-triangle me-2"></i>${data.error || 'Failed to load pinned memories'}
                </div>
            `;
        }
    })
    .catch(error => {
        console.error('Error fetching pinned memories:', error);
        document.getElementById('pinnedMemoriesList').innerHTML = `
            <div class="text-center p-3 text-muted">
                <i class="bi bi-exclamation-triangle me-2"></i>Error loading pinned memories
            </div>
        `;
    });
}

/**
 * Load session summary
 */
function loadSessionSummary() {
    if (!currentSessionId) {
        console.error('No session ID for loading summary');
        return;
    }
    
    // Get CSRF token from meta tag
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    
    // Fetch summary from API
    fetch(`/api/summary/${currentSessionId}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            console.log('Loaded session summary');
            // Render summary
            document.getElementById('sessionSummary').innerHTML = data.summary;
        } else {
            console.error('Error loading summary:', data.error);
            document.getElementById('sessionSummary').innerHTML = `
                <div class="text-center text-muted">
                    <i class="bi bi-exclamation-triangle me-2"></i>${data.error || 'Failed to load summary'}
                </div>
            `;
        }
    })
    .catch(error => {
        console.error('Error fetching summary:', error);
        document.getElementById('sessionSummary').innerHTML = `
            <div class="text-center text-muted">
                <i class="bi bi-exclamation-triangle me-2"></i>Error loading summary
            </div>
        `;
    });
}

/**
 * Process memories and organize them
 * @param {Array} memories - List of memory objects
 */
function processMemories(memories) {
    // Identify pinned memories
    const sessionResult = getSessionFromDOM();
    if (sessionResult.success) {
        const session = sessionResult.session;
        pinnedMemories = [];
        
        // Check if session has pinned_memories
        if (session.pinned_memories && session.pinned_memories.length > 0) {
            // Find memories that match pinned memory IDs
            const pinnedIds = session.pinned_memories.map(p => p.memory_id);
            
            pinnedMemories = memories.filter(memory => pinnedIds.includes(memory.memory_id));
        }
        
        // Render pinned memories
        renderPinnedMemories(pinnedMemories);
    }
}

/**
 * Render entities in the UI
 * @param {Object} entities - Entity objects
 */
function renderEntities(entities) {
    const entitiesList = document.getElementById('entitiesList');
    if (!entitiesList) return;
    
    // Clear current list
    entitiesList.innerHTML = '';
    
    if (Object.keys(entities).length === 0) {
        entitiesList.innerHTML = `
            <div class="text-center p-3 text-muted">
                <i class="bi bi-info-circle me-2"></i>No entities detected yet
            </div>
        `;
        return;
    }
    
    // Convert to array for sorting
    const entitiesArray = Object.entries(entities).map(([name, data]) => ({
        name,
        ...data
    }));
    
    // Sort by importance (highest first)
    entitiesArray.sort((a, b) => (b.importance || 5) - (a.importance || 5));
    
    // Create list items
    entitiesArray.forEach(entity => {
        const listItem = document.createElement('div');
        listItem.className = 'list-group-item list-group-item-action bg-dark text-light border-secondary entity-item';
        listItem.setAttribute('data-entity-type', entity.type || 'unknown');
        
        // Icon based on entity type
        let icon = 'bi-question-circle';
        if (entity.type === 'npc') icon = 'bi-person';
        else if (entity.type === 'location') icon = 'bi-geo-alt';
        else if (entity.type === 'item') icon = 'bi-box';
        
        // Create HTML content
        listItem.innerHTML = `
            <div class="d-flex justify-content-between align-items-start">
                <div>
                    <div class="d-flex align-items-center">
                        <i class="bi ${icon} me-2"></i>
                        <h6 class="mb-0">${entity.name}</h6>
                        <span class="badge bg-secondary ms-2">${entity.type || 'unknown'}</span>
                    </div>
                    <div class="small text-muted mt-1">${entity.description || 'No description available'}</div>
                </div>
                <div>
                    <div class="entity-importance" title="Importance: ${entity.importance || 5}">
                        ${getImportanceStars(entity.importance || 5)}
                    </div>
                </div>
            </div>
        `;
        
        // Add click handler to copy to input
        listItem.addEventListener('click', function() {
            const playerInput = document.getElementById('playerInput');
            if (playerInput) {
                // Insert entity name at cursor position or append to end
                insertAtCursor(playerInput, entity.name);
                // Focus input
                playerInput.focus();
            }
        });
        
        // Add context menu for editing
        listItem.addEventListener('contextmenu', function(e) {
            e.preventDefault();
            showEntityContextMenu(e, entity);
        });
        
        entitiesList.appendChild(listItem);
    });
}

/**
 * Render pinned memories in the UI
 * @param {Array} memories - List of pinned memory objects
 */
function renderPinnedMemories(memories) {
    const pinnedList = document.getElementById('pinnedMemoriesList');
    if (!pinnedList) return;
    
    // Clear current list
    pinnedList.innerHTML = '';
    
    if (memories.length === 0) {
        pinnedList.innerHTML = `
            <div class="text-center p-3 text-muted">
                <i class="bi bi-info-circle me-2"></i>No pinned memories yet
            </div>
        `;
        return;
    }
    
    // Sort by importance (highest first)
    memories.sort((a, b) => (b.importance || 5) - (a.importance || 5));
    
    // Create list items
    memories.forEach(memory => {
        const listItem = document.createElement('div');
        listItem.className = 'list-group-item bg-dark text-light border-secondary memory-item';
        
        // Icon based on sender
        let icon = 'bi-bookmark';
        if (memory.metadata && memory.metadata.sender === 'player') {
            icon = 'bi-person-circle';
        } else if (memory.metadata && memory.metadata.sender === 'dm') {
            icon = 'bi-robot';
        }
        
        // Truncate content if too long
        const content = memory.content.length > 150 ? 
                        memory.content.substring(0, 150) + '...' : 
                        memory.content;
        
        // Format timestamp
        const timestamp = new Date(memory.created_at).toLocaleString();
        
        // Create HTML content
        listItem.innerHTML = `
            <div class="d-flex justify-content-between align-items-start">
                <div>
                    <div class="d-flex align-items-center">
                        <i class="bi ${icon} me-2"></i>
                        <span class="badge bg-${getMemoryTypeColor(memory.memory_type)}">${memory.memory_type}</span>
                    </div>
                    <div class="mt-1">${content}</div>
                    <div class="small text-muted mt-1">${timestamp}</div>
                </div>
                <div>
                    <button class="btn btn-sm btn-outline-danger unpin-btn" data-memory-id="${memory.memory_id}">
                        <i class="bi bi-x"></i>
                    </button>
                </div>
            </div>
        `;
        
        // Add unpin button click handler
        listItem.querySelector('.unpin-btn').addEventListener('click', function(e) {
            e.stopPropagation();
            const memoryId = this.getAttribute('data-memory-id');
            unpinMemory(memoryId);
        });
        
        // Add click handler to copy to input
        listItem.addEventListener('click', function() {
            const playerInput = document.getElementById('playerInput');
            if (playerInput) {
                // Insert memory content at cursor position or append to end
                insertAtCursor(playerInput, memory.content);
                // Focus input
                playerInput.focus();
            }
        });
        
        pinnedList.appendChild(listItem);
    });
}

/**
 * Filter entities by type
 * @param {string} filterType - Type to filter by
 */
function filterEntities(filterType) {
    const entities = document.querySelectorAll('.entity-item');
    
    entities.forEach(entity => {
        const entityType = entity.getAttribute('data-entity-type');
        
        if (filterType === 'all' || entityType === filterType) {
            entity.style.display = '';
        } else {
            entity.style.display = 'none';
        }
    });
}

/**
 * Show context menu for entity editing
 * @param {Event} e - Mouse event
 * @param {Object} entity - Entity object
 */
function showEntityContextMenu(e, entity) {
    // Remove any existing context menu
    const existingMenu = document.getElementById('entityContextMenu');
    if (existingMenu) {
        existingMenu.remove();
    }
    
    // Create context menu
    const contextMenu = document.createElement('div');
    contextMenu.id = 'entityContextMenu';
    contextMenu.className = 'bg-dark text-light border border-secondary rounded shadow-lg p-2';
    contextMenu.style.position = 'fixed';
    contextMenu.style.zIndex = '1000';
    contextMenu.style.top = `${e.clientY}px`;
    contextMenu.style.left = `${e.clientX}px`;
    contextMenu.style.minWidth = '200px';
    
    // Menu items
    contextMenu.innerHTML = `
        <div class="context-item p-2 d-flex align-items-center" data-action="edit">
            <i class="bi bi-pencil me-2"></i>Edit Entity
        </div>
        <div class="context-item p-2 d-flex align-items-center" data-action="pin">
            <i class="bi bi-pin-angle me-2"></i>Pin to Memory
        </div>
        <div class="context-item p-2 d-flex align-items-center text-danger" data-action="delete">
            <i class="bi bi-trash me-2"></i>Delete Entity
        </div>
    `;
    
    // Add click handlers
    contextMenu.querySelectorAll('.context-item').forEach(item => {
        item.addEventListener('click', function() {
            const action = this.getAttribute('data-action');
            handleEntityAction(action, entity);
            contextMenu.remove();
        });
        
        // Add hover effect
        item.addEventListener('mouseenter', function() {
            this.classList.add('bg-primary');
        });
        
        item.addEventListener('mouseleave', function() {
            this.classList.remove('bg-primary');
        });
    });
    
    // Add to document
    document.body.appendChild(contextMenu);
    
    // Click outside to close
    document.addEventListener('click', function closeMenu(e) {
        if (!contextMenu.contains(e.target)) {
            contextMenu.remove();
            document.removeEventListener('click', closeMenu);
        }
    });
}

/**
 * Handle entity context menu actions
 * @param {string} action - Action to perform
 * @param {Object} entity - Entity object
 */
function handleEntityAction(action, entity) {
    if (action === 'edit') {
        showEntityEditModal(entity);
    } else if (action === 'pin') {
        // Create a memory from entity
        const content = `Entity: ${entity.name} (${entity.type}): ${entity.description}`;
        pinEntityAsMemory(entity.name, content, entity.importance);
    } else if (action === 'delete') {
        if (confirm(`Are you sure you want to delete the entity "${entity.name}"?`)) {
            deleteEntity(entity.name);
        }
    }
}

/**
 * Show modal for editing an entity
 * @param {Object} entity - Entity object
 */
function showEntityEditModal(entity) {
    // Remove existing modal if any
    const existingModal = document.getElementById('entityEditModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Create modal
    const modal = document.createElement('div');
    modal.id = 'entityEditModal';
    modal.className = 'modal fade';
    modal.tabIndex = '-1';
    modal.setAttribute('aria-labelledby', 'entityEditModalLabel');
    modal.setAttribute('aria-hidden', 'true');
    
    // Modal content
    modal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content bg-dark text-light">
                <div class="modal-header">
                    <h5 class="modal-title" id="entityEditModalLabel">Edit Entity: ${entity.name}</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <form id="entityEditForm">
                        <div class="mb-3">
                            <label for="entityName" class="form-label">Name</label>
                            <input type="text" class="form-control bg-dark text-light border-secondary" id="entityName" value="${entity.name}" readonly>
                        </div>
                        <div class="mb-3">
                            <label for="entityType" class="form-label">Type</label>
                            <select class="form-select bg-dark text-light border-secondary" id="entityType">
                                <option value="npc" ${entity.type === 'npc' ? 'selected' : ''}>NPC</option>
                                <option value="location" ${entity.type === 'location' ? 'selected' : ''}>Location</option>
                                <option value="item" ${entity.type === 'item' ? 'selected' : ''}>Item</option>
                                <option value="unknown" ${entity.type === 'unknown' ? 'selected' : ''}>Other</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label for="entityDescription" class="form-label">Description</label>
                            <textarea class="form-control bg-dark text-light border-secondary" id="entityDescription" rows="3">${entity.description || ''}</textarea>
                        </div>
                        <div class="mb-3">
                            <label for="entityImportance" class="form-label">Importance (1-10): ${entity.importance || 5}</label>
                            <input type="range" class="form-range" min="1" max="10" id="entityImportance" value="${entity.importance || 5}">
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-primary" id="saveEntityBtn">Save Changes</button>
                </div>
            </div>
        </div>
    `;
    
    // Add to document
    document.body.appendChild(modal);
    
    // Initialize Bootstrap modal
    const modalInstance = new bootstrap.Modal(modal);
    
    // Show modal
    modalInstance.show();
    
    // Add event listener for importance slider
    const importanceSlider = document.getElementById('entityImportance');
    const importanceLabel = document.querySelector('label[for="entityImportance"]');
    
    importanceSlider.addEventListener('input', function() {
        importanceLabel.textContent = `Importance (1-10): ${this.value}`;
    });
    
    // Add event listener for save button
    document.getElementById('saveEntityBtn').addEventListener('click', function() {
        const updatedEntity = {
            type: document.getElementById('entityType').value,
            description: document.getElementById('entityDescription').value,
            importance: parseInt(document.getElementById('entityImportance').value)
        };
        
        // Update entity in database
        updateEntity(entity.name, updatedEntity, modalInstance);
    });
}

/**
 * Update an entity in the database
 * @param {string} entityName - Entity name
 * @param {Object} entityData - Updated entity data
 * @param {Object} modal - Bootstrap modal instance
 */
function updateEntity(entityName, entityData, modal) {
    if (!currentSessionId) {
        alert('No active session found');
        return;
    }
    
    // Get CSRF token from meta tag
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    
    // Send update request
    fetch(`/api/entities/${currentSessionId}/update`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            name: entityName,
            data: entityData
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Hide modal
            modal.hide();
            
            // Reload entities
            loadSessionEntities();
            
            // Show success message
            showToast('Entity updated successfully', 'success');
        } else {
            console.error('Error updating entity:', data.error);
            alert(`Error updating entity: ${data.error || 'Unknown error'}`);
        }
    })
    .catch(error => {
        console.error('Error updating entity:', error);
        alert(`Error updating entity: ${error.message}`);
    });
}

/**
 * Delete an entity
 * @param {string} entityName - Entity name
 */
function deleteEntity(entityName) {
    if (!currentSessionId) {
        alert('No active session found');
        return;
    }
    
    // Get CSRF token from meta tag
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    
    // Send delete request
    fetch(`/api/entities/${currentSessionId}/update`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            name: entityName,
            data: { deleted: true }
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Reload entities
            loadSessionEntities();
            
            // Show success message
            showToast('Entity deleted successfully', 'success');
        } else {
            console.error('Error deleting entity:', data.error);
            alert(`Error deleting entity: ${data.error || 'Unknown error'}`);
        }
    })
    .catch(error => {
        console.error('Error deleting entity:', error);
        alert(`Error deleting entity: ${error.message}`);
    });
}

/**
 * Pin a memory to the session
 * @param {string} memoryId - Memory ID
 * @param {number} importance - Optional importance override
 * @param {string} note - Optional note
 */
function pinMemory(memoryId, importance = null, note = null) {
    if (!currentSessionId) {
        alert('No active session found');
        return;
    }
    
    // Get CSRF token from meta tag
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    
    // Send pin request
    fetch(`/api/memories/${currentSessionId}/pin`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            memory_id: memoryId,
            importance: importance,
            note: note
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Reload pinned memories
            loadPinnedMemories();
            
            // Show success message
            showToast('Memory pinned successfully', 'success');
        } else {
            console.error('Error pinning memory:', data.error);
            alert(`Error pinning memory: ${data.error || 'Unknown error'}`);
        }
    })
    .catch(error => {
        console.error('Error pinning memory:', error);
        alert(`Error pinning memory: ${error.message}`);
    });
}

/**
 * Unpin a memory from the session
 * @param {string} memoryId - Memory ID
 */
function unpinMemory(memoryId) {
    if (!currentSessionId) {
        alert('No active session found');
        return;
    }
    
    // Get CSRF token from meta tag
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    
    // Send unpin request
    fetch(`/api/memories/${currentSessionId}/unpin`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            memory_id: memoryId
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Reload pinned memories
            loadPinnedMemories();
            
            // Show success message
            showToast('Memory unpinned successfully', 'success');
        } else {
            console.error('Error unpinning memory:', data.error);
            alert(`Error unpinning memory: ${data.error || 'Unknown error'}`);
        }
    })
    .catch(error => {
        console.error('Error unpinning memory:', error);
        alert(`Error unpinning memory: ${error.message}`);
    });
}

/**
 * Pin an entity as a memory
 * @param {string} entityName - Entity name
 * @param {string} content - Memory content
 * @param {number} importance - Importance score
 */
function pinEntityAsMemory(entityName, content, importance) {
    if (!currentSessionId) {
        alert('No active session found');
        return;
    }
    
    // Get CSRF token from meta tag
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    
    // Create and store a new memory
    fetch(`/api/memories/${currentSessionId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            content: content,
            memory_type: 'long_term',
            importance: importance,
            metadata: {
                entity_name: entityName,
                pinned: true
            }
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Pin the new memory
            pinMemory(data.memory_id, importance, `Entity: ${entityName}`);
        } else {
            console.error('Error creating memory from entity:', data.error);
            alert(`Error creating memory: ${data.error || 'Unknown error'}`);
        }
    })
    .catch(error => {
        console.error('Error creating memory from entity:', error);
        alert(`Error creating memory: ${error.message}`);
    });
}

/**
 * Get importance stars for display
 * @param {number} importance - Importance score (1-10)
 * @returns {string} HTML string with stars
 */
function getImportanceStars(importance) {
    // Normalize to 1-5 stars
    const stars = Math.ceil(importance / 2);
    
    let html = '';
    for (let i = 0; i < 5; i++) {
        if (i < stars) {
            html += '<i class="bi bi-star-fill text-warning"></i>';
        } else {
            html += '<i class="bi bi-star text-muted"></i>';
        }
    }
    
    return html;
}

/**
 * Get color for memory type badge
 * @param {string} memoryType - Memory type
 * @returns {string} Bootstrap color class
 */
function getMemoryTypeColor(memoryType) {
    switch (memoryType) {
        case 'short_term':
            return 'info';
        case 'long_term':
            return 'primary';
        case 'summary':
            return 'success';
        case 'semantic':
            return 'warning';
        default:
            return 'secondary';
    }
}

/**
 * Insert text at cursor position in input field
 * @param {HTMLElement} input - Input element
 * @param {string} text - Text to insert
 */
function insertAtCursor(input, text) {
    const startPos = input.selectionStart;
    const endPos = input.selectionEnd;
    const beforeText = input.value.substring(0, startPos);
    const afterText = input.value.substring(endPos, input.value.length);
    
    // Insert with proper spacing
    let insertText = text;
    if (beforeText && !beforeText.endsWith(' ')) {
        insertText = ' ' + insertText;
    }
    if (afterText && !afterText.startsWith(' ')) {
        insertText = insertText + ' ';
    }
    
    input.value = beforeText + insertText + afterText;
    
    // Set cursor position after inserted text
    const newPos = startPos + insertText.length;
    input.setSelectionRange(newPos, newPos);
}

/**
 * Show a toast notification
 * @param {string} message - Notification message
 * @param {string} type - Notification type (success, error, warning, info)
 */
function showToast(message, type = 'info') {
    // Remove existing toast container if any
    const existingContainer = document.getElementById('toastContainer');
    if (existingContainer) {
        existingContainer.remove();
    }
    
    // Create container
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'position-fixed top-0 end-0 p-3';
    container.style.zIndex = '1070';
    
    // Create toast
    container.innerHTML = `
        <div class="toast bg-dark text-light" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header bg-${type === 'error' ? 'danger' : type} text-light">
                <strong class="me-auto">Memory System</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    // Add to document
    document.body.appendChild(container);
    
    // Initialize and show Bootstrap toast
    const toastEl = container.querySelector('.toast');
    const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
    toast.show();
}

/**
 * Get session data from DOM
 * @returns {Object} Session object
 */
function getSessionFromDOM() {
    try {
        const sessionDataEl = document.getElementById('sessionData');
        if (sessionDataEl) {
            return {
                success: true,
                session: JSON.parse(sessionDataEl.textContent)
            };
        } else {
            return {
                success: false,
                error: 'Session data element not found'
            };
        }
    } catch (error) {
        console.error('Error parsing session data:', error);
        return {
            success: false,
            error: 'Error parsing session data'
        };
    }
}

/**
 * Patch the sendMessage function to capture session ID
 */
function patchSendMessageFunction() {
    // Check if window.sendMessage exists
    if (typeof window.sendMessage === 'function') {
        // Save original function
        const originalSendMessage = window.sendMessage;
        
        // Create new function
        window.sendMessage = function() {
            // Call original function
            originalSendMessage.apply(this, arguments);
            
            // Add event listener for response
            document.addEventListener('dm-response-received', function captureSession(event) {
                if (event.detail && event.detail.session_id) {
                    currentSessionId = event.detail.session_id;
                    console.log('Captured session ID:', currentSessionId);
                    
                    // Set session ID on chat window for persistence
                    const chatWindow = document.getElementById('chatWindow');
                    if (chatWindow) {
                        chatWindow.setAttribute('data-session-id', currentSessionId);
                    }
                    
                    // Remove this event listener to avoid duplicates
                    document.removeEventListener('dm-response-received', captureSession);
                    
                    // Load memory data
                    loadSessionMemories();
                    loadSessionEntities();
                }
            });
        };
    }
}