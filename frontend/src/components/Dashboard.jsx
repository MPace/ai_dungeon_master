// File: frontend/src/components/Dashboard.jsx

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import './Dashboard.css';

function Dashboard() {
    const [characters, setCharacters] = useState([]);
    const [drafts, setDrafts] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const [sortField, setSortField] = useState('last_played');
    const [sortDirection, setSortDirection] = useState('desc');
    const [filterText, setFilterText] = useState('');
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [deleteItemId, setDeleteItemId] = useState(null);
    const [deleteItemType, setDeleteItemType] = useState(null);
    const [deleteItemName, setDeleteItemName] = useState('');
    const [flashMessage, setFlashMessage] = useState(null);

    // Fetch characters and drafts on component mount
    useEffect(() => {
        fetchCharacters();
        fetchDrafts();
    }, []);

    // Format date helper function
    const formatDate = (dateString) => {
        if (!dateString) return 'Never';
        
        const date = new Date(dateString);
        if (isNaN(date.getTime())) return dateString;
        
        return date.toLocaleString('en-GB', {
            day: '2-digit',
            month: '2-digit',
            year: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
        });
    };

    // Fetch characters from API
    const fetchCharacters = async () => {
        try {
            setIsLoading(true);
            const response = await fetch('/api/characters');
            
            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                setCharacters(data.characters || []);
            } else {
                throw new Error(data.error || 'Failed to load characters');
            }
        } catch (err) {
            console.error('Error fetching characters:', err);
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    // Fetch drafts from API
    const fetchDrafts = async () => {
        try {
            const response = await fetch('/api/drafts');
            
            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                setDrafts(data.drafts || []);
            } else {
                throw new Error(data.error || 'Failed to load drafts');
            }
        } catch (err) {
            console.error('Error fetching drafts:', err);
            // We don't set the error state here to avoid blocking the UI if only drafts fail
        }
    };

    // Delete character handler
    const handleDeleteCharacter = async (characterId) => {
        try {
            // Get CSRF token
            const tokenMeta = document.querySelector('meta[name="csrf-token"]');
            const csrfToken = tokenMeta ? tokenMeta.getAttribute('content') : '';
            
            const response = await fetch(`/api/delete-character/${characterId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ character_id: characterId })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Update state to remove the deleted character
                setCharacters(prevCharacters => 
                    prevCharacters.filter(char => char.character_id !== characterId)
                );
                setFlashMessage({
                    type: 'success',
                    text: data.message || 'Character deleted successfully'
                });
            } else {
                throw new Error(data.error || 'Failed to delete character');
            }
        } catch (err) {
            console.error('Error deleting character:', err);
            setFlashMessage({
                type: 'danger',
                text: `Error: ${err.message}`
            });
        } finally {
            setShowDeleteModal(false);
        }
    };

    // Delete draft handler
    const handleDeleteDraft = async (draftId) => {
        try {
            // Get CSRF token
            const tokenMeta = document.querySelector('meta[name="csrf-token"]');
            const csrfToken = tokenMeta ? tokenMeta.getAttribute('content') : '';
            
            const response = await fetch(`/api/delete-draft/${draftId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ draft_id: draftId })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Update state to remove the deleted draft
                setDrafts(prevDrafts => 
                    prevDrafts.filter(draft => draft.character_id !== draftId)
                );
                setFlashMessage({
                    type: 'success',
                    text: data.message || 'Draft deleted successfully'
                });
            } else {
                throw new Error(data.error || 'Failed to delete draft');
            }
        } catch (err) {
            console.error('Error deleting draft:', err);
            setFlashMessage({
                type: 'danger',
                text: `Error: ${err.message}`
            });
        } finally {
            setShowDeleteModal(false);
        }
    };

    // Confirmation modal open handler
    const openDeleteModal = (id, type, name) => {
        setDeleteItemId(id);
        setDeleteItemType(type);
        setDeleteItemName(name || 'Unnamed');
        setShowDeleteModal(true);
    };

    // Sort handler
    const handleSort = (field) => {
        if (sortField === field) {
            // Toggle direction if clicking the same field
            setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
        } else {
            // Set new field and default to descending
            setSortField(field);
            setSortDirection('desc');
        }
    };

    // Apply sorting and filtering to characters
    const sortedFilteredCharacters = [...characters]
        .filter(char => {
            if (!filterText) return true;
            const searchText = filterText.toLowerCase();
            return (
                (char.name && char.name.toLowerCase().includes(searchText)) ||
                (char.race && char.race.toLowerCase().includes(searchText)) ||
                (char.character_class && char.character_class.toLowerCase().includes(searchText)) ||
                (char.worldName && char.worldName.toLowerCase().includes(searchText))
            );
        })
        .sort((a, b) => {
            // Fallbacks for null values
            const valA = a[sortField] || '';
            const valB = b[sortField] || '';
            
            // Sort logic
            if (sortField === 'last_played' || sortField === 'created_at') {
                // Date comparison
                const dateA = valA ? new Date(valA).getTime() : 0;
                const dateB = valB ? new Date(valB).getTime() : 0;
                return sortDirection === 'asc' ? dateA - dateB : dateB - dateA;
            } else {
                // String comparison
                return sortDirection === 'asc' 
                    ? String(valA).localeCompare(String(valB))
                    : String(valB).localeCompare(String(valA));
            }
        });

    // Handle dismissing flash messages
    const dismissFlash = () => {
        setFlashMessage(null);
    };

    return (
        <div className="dashboard-container">
            {/* Header */}
            <header className="dashboard-header text-center mb-4">
                <h1 className="display-4 text-light">Your Adventures</h1>
                <p className="lead text-light">Manage your characters and campaigns</p>
            </header>
            
            {/* Flash Messages */}
            {flashMessage && (
                <div className={`alert alert-${flashMessage.type} alert-dismissible fade show`} role="alert">
                    {flashMessage.text}
                    <button 
                        type="button" 
                        className="btn-close" 
                        onClick={dismissFlash} 
                        aria-label="Close"
                    ></button>
                </div>
            )}
            
            {/* Loading and Error States */}
            {isLoading && (
                <div className="text-center text-light p-5">
                    <div className="spinner-border text-primary" role="status">
                        <span className="visually-hidden">Loading...</span>
                    </div>
                    <p className="mt-3">Loading your characters...</p>
                </div>
            )}
            
            {error && !isLoading && (
                <div className="alert alert-danger" role="alert">
                    {error}
                </div>
            )}
            
            {/* Main Content */}
            {!isLoading && !error && (
                <div className="dashboard-content">
                    {/* Create New Character Card */}
                    <div className="card new-adventure-card mb-4">
                        <div className="card-header bg-dark text-light d-flex justify-content-between align-items-center">
                            <h3 className="mb-0"><i className="bi bi-plus-circle me-2"></i>New Adventure</h3>
                        </div>
                        <div className="card-body bg-dark text-light text-center py-5">
                            <h4 className="mb-4">Begin a new quest with a fresh character</h4>
                            <Link to="/characters/create" className="btn btn-lg btn-primary px-4 py-3">
                                <i className="bi bi-person-plus me-2"></i>Create New Character
                            </Link>
                        </div>
                    </div>
                    
                    {/* Characters List */}
                    <div className="card character-list-card mb-4">
                        <div className="card-header bg-dark text-light d-flex justify-content-between align-items-center">
                            <h3 className="mb-0"><i className="bi bi-people me-2"></i>Your Characters</h3>
                            <span className="badge bg-primary">{sortedFilteredCharacters.length}</span>
                        </div>
                        
                        {/* Search and Sort Controls */}
                        <div className="card-body bg-dark p-3 border-bottom border-secondary">
                            <div className="row align-items-center">
                                <div className="col-md-6 mb-3 mb-md-0">
                                    <div className="input-group">
                                        <span className="input-group-text bg-dark text-light border-secondary">
                                            <i className="bi bi-search"></i>
                                        </span>
                                        <input 
                                            type="text" 
                                            className="form-control bg-dark text-light border-secondary" 
                                            placeholder="Search characters..." 
                                            value={filterText}
                                            onChange={(e) => setFilterText(e.target.value)}
                                        />
                                    </div>
                                </div>
                                <div className="col-md-6">
                                    <div className="d-flex justify-content-md-end">
                                        <select 
                                            className="form-select bg-dark text-light border-secondary me-2" 
                                            value={`${sortField}-${sortDirection}`}
                                            onChange={(e) => {
                                                const [field, direction] = e.target.value.split('-');
                                                setSortField(field);
                                                setSortDirection(direction);
                                            }}
                                            style={{maxWidth: '200px'}}
                                        >
                                            <option value="last_played-desc">Latest Played</option>
                                            <option value="last_played-asc">Oldest Played</option>
                                            <option value="name-asc">Name (A-Z)</option>
                                            <option value="name-desc">Name (Z-A)</option>
                                            <option value="level-desc">Level (High-Low)</option>
                                            <option value="level-asc">Level (Low-High)</option>
                                            <option value="character_class-asc">Class (A-Z)</option>
                                            <option value="race-asc">Race (A-Z)</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        {sortedFilteredCharacters.length > 0 ? (
                            <div className="table-responsive">
                                <table className="table table-dark table-hover mb-0 characters-table">
                                    <thead>
                                        <tr>
                                            <th onClick={() => handleSort('name')} style={{cursor: 'pointer'}}>
                                                Name {sortField === 'name' && (
                                                    <i className={`bi bi-caret-${sortDirection === 'asc' ? 'up' : 'down'}-fill ms-1`}></i>
                                                )}
                                            </th>
                                            <th onClick={() => handleSort('race')} style={{cursor: 'pointer'}}>
                                                Race {sortField === 'race' && (
                                                    <i className={`bi bi-caret-${sortDirection === 'asc' ? 'up' : 'down'}-fill ms-1`}></i>
                                                )}
                                            </th>
                                            <th onClick={() => handleSort('character_class')} style={{cursor: 'pointer'}}>
                                                Class {sortField === 'character_class' && (
                                                    <i className={`bi bi-caret-${sortDirection === 'asc' ? 'up' : 'down'}-fill ms-1`}></i>
                                                )}
                                            </th>
                                            <th onClick={() => handleSort('level')} style={{cursor: 'pointer'}}>
                                                Level {sortField === 'level' && (
                                                    <i className={`bi bi-caret-${sortDirection === 'asc' ? 'up' : 'down'}-fill ms-1`}></i>
                                                )}
                                            </th>
                                            <th onClick={() => handleSort('worldName')} style={{cursor: 'pointer'}}>
                                                World {sortField === 'worldName' && (
                                                    <i className={`bi bi-caret-${sortDirection === 'asc' ? 'up' : 'down'}-fill ms-1`}></i>
                                                )}
                                            </th>
                                            <th onClick={() => handleSort('last_played')} style={{cursor: 'pointer'}}>
                                                Last Played {sortField === 'last_played' && (
                                                    <i className={`bi bi-caret-${sortDirection === 'asc' ? 'up' : 'down'}-fill ms-1`}></i>
                                                )}
                                            </th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {sortedFilteredCharacters.map(character => (
                                            <tr key={character.character_id} data-character-id={character.character_id}>
                                                <td className="align-middle">{character.name}</td>
                                                <td className="align-middle">{character.race}</td>
                                                <td className="align-middle">{character.character_class}</td>
                                                <td className="align-middle">{character.level}</td>
                                                <td className="align-middle">{character.worldName || 'Unknown'}</td>
                                                <td className="align-middle">{formatDate(character.last_played)}</td>
                                                <td>
                                                    <div className="btn-group">
                                                        <Link 
                                                            to={`/game/play/${character.character_id}`} 
                                                            className="btn btn-sm btn-success"
                                                        >
                                                            <i className="bi bi-play-fill"></i> Play
                                                        </Link>
                                                        <button 
                                                            type="button" 
                                                            className="btn btn-sm btn-secondary dropdown-toggle dropdown-toggle-split" 
                                                            data-bs-toggle="dropdown"
                                                        ></button>
                                                        <ul className="dropdown-menu dropdown-menu-end">
                                                            <li>
                                                                <a className="dropdown-item" href="#">
                                                                    <i className="bi bi-pencil me-2"></i>Edit
                                                                </a>
                                                            </li>
                                                            <li><hr className="dropdown-divider" /></li>
                                                            <li>
                                                                <button 
                                                                    className="dropdown-item text-danger"
                                                                    onClick={() => openDeleteModal(
                                                                        character.character_id,
                                                                        'character',
                                                                        character.name
                                                                    )}
                                                                >
                                                                    <i className="bi bi-trash me-2"></i>Delete
                                                                </button>
                                                            </li>
                                                        </ul>
                                                    </div>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        ) : (
                            <div className="p-4 text-center text-light">
                                <p className="mb-0">You haven't created any characters yet.</p>
                            </div>
                        )}
                    </div>
                    
                    {/* Drafts List */}
                    {drafts.length > 0 && (
                        <div className="card draft-list-card mb-4">
                            <div className="card-header bg-dark text-light d-flex justify-content-between align-items-center">
                                <h3 className="mb-0"><i className="bi bi-file-earmark-text me-2"></i>Drafts</h3>
                                <span className="badge bg-warning text-dark">{drafts.length}</span>
                            </div>
                            <div className="card-body bg-dark text-light p-0">
                                <table className="table table-dark table-hover mb-0 drafts-table">
                                    <thead>
                                        <tr>
                                            <th>Name</th>
                                            <th>Race</th>
                                            <th>Class</th>
                                            <th>Creation Step</th>
                                            <th>Updated</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {drafts.map(draft => (
                                            <tr key={draft.character_id} data-draft-id={draft.character_id}>
                                                <td className="align-middle">{draft.name || 'Unnamed'}</td>
                                                <td className="align-middle">{draft.race || '-'}</td>
                                                <td className="align-middle">{draft.character_class || '-'}</td>
                                                <td className="align-middle">{draft.lastStep || '1'}/8</td>
                                                <td className="align-middle">{formatDate(draft.lastUpdated)}</td>
                                                <td>
                                                    <div className="btn-group">
                                                        <Link 
                                                            to={`/characters/create?draft_id=${draft.character_id}`} 
                                                            className="btn btn-sm btn-warning text-dark"
                                                        >
                                                            <i className="bi bi-pencil-fill"></i> Continue
                                                        </Link>
                                                        <button 
                                                            type="button" 
                                                            className="btn btn-sm btn-warning text-dark dropdown-toggle dropdown-toggle-split" 
                                                            data-bs-toggle="dropdown"
                                                        ></button>
                                                        <ul className="dropdown-menu dropdown-menu-end">
                                                            <li>
                                                                <button 
                                                                    className="dropdown-item text-danger"
                                                                    onClick={() => openDeleteModal(
                                                                        draft.character_id,
                                                                        'draft',
                                                                        draft.name || 'Unnamed draft'
                                                                    )}
                                                                >
                                                                    <i className="bi bi-trash me-2"></i>Delete
                                                                </button>
                                                            </li>
                                                        </ul>
                                                    </div>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}
                </div>
            )}
            
            {/* Delete Confirmation Modal */}
            {showDeleteModal && (
                <div className="modal show" style={{display: 'block', backgroundColor: 'rgba(0,0,0,0.5)'}}>
                    <div className="modal-dialog">
                        <div className="modal-content bg-dark text-light">
                            <div className="modal-header border-secondary">
                                <h5 className="modal-title">Confirm Delete</h5>
                                <button 
                                    type="button" 
                                    className="btn-close btn-close-white" 
                                    onClick={() => setShowDeleteModal(false)}
                                    aria-label="Close"
                                ></button>
                            </div>
                            <div className="modal-body">
                                <p>Are you sure you want to delete "{deleteItemName}"?</p>
                                <p className="text-danger">This action cannot be undone.</p>
                            </div>
                            <div className="modal-footer border-secondary">
                                <button 
                                    type="button" 
                                    className="btn btn-secondary" 
                                    onClick={() => setShowDeleteModal(false)}
                                >
                                    Cancel
                                </button>
                                <button 
                                    type="button" 
                                    className="btn btn-danger" 
                                    onClick={() => 
                                        deleteItemType === 'character' 
                                            ? handleDeleteCharacter(deleteItemId) 
                                            : handleDeleteDraft(deleteItemId)
                                    }
                                >
                                    Delete
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default Dashboard;