// File: frontend/src/components/Dashboard.jsx

import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
    getCharacters, 
    getDrafts, 
    deleteCharacter, 
    deleteDraft 
} from '../services/api';
import './Dashboard.css';

// Helper function to format date
const formatDate = (dateString) => {
    if (!dateString) return 'Never';
    
    try {
        const date = new Date(dateString);
        if (isNaN(date.getTime())) return dateString;
        
        // Format as DD/MM/YY HH:MM
        return date.toLocaleDateString('en-GB', {
            day: '2-digit',
            month: '2-digit',
            year: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        }).replace(',', '');
    } catch {
        return dateString;
    }
};

const Dashboard = () => {
    const [characters, setCharacters] = useState([]);
    const [drafts, setDrafts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [alertMessage, setAlertMessage] = useState(null);
    const [sortField, setSortField] = useState('last_played');
    const [sortDirection, setSortDirection] = useState('desc');
    const [filter, setFilter] = useState('');
    
    const navigate = useNavigate();
    
    // Get username from meta tag
    const username = document.querySelector('meta[name="username"]')?.getAttribute('content') || 'User';

    // Load data
    const loadData = async () => {
        setLoading(true);
        try {
            // Fetch characters
            const charactersResponse = await getCharacters();
            if (charactersResponse.success) {
                // Process characters to ensure they have consistent properties
                const processedCharacters = (charactersResponse.characters || []).map(character => {
                    // Normalize the data structure by mapping properties
                    return {
                        ...character,
                        // Ensure character_class is available (might be in class or character_class)
                        character_class: character.character_class || character.class || character.className || '',
                        // World info might be in worldId/worldName or in a nested structure
                        worldName: character.worldName || 
                                 (character.worldId ? `World ${character.worldId}` : '-'),
                        // Campaign info might be in campaignId/campaignName or in a nested structure
                        campaignName: character.campaignName || 
                                    (character.campaignId ? `Campaign ${character.campaignId}` : '-')
                    };
                });
                setCharacters(processedCharacters);
                console.log("Processed characters:", processedCharacters);
            } else {
                throw new Error(charactersResponse.error || 'Failed to load characters');
            }
            
            // Fetch drafts
            const draftsResponse = await getDrafts();
            if (draftsResponse.success) {
                // Process drafts to ensure they have consistent properties
                const processedDrafts = (draftsResponse.drafts || []).map(draft => {
                    return {
                        ...draft,
                        // Ensure character_class is available (might be in class or character_class)
                        character_class: draft.character_class || draft.class || draft.className || '',
                        // Ensure lastStepCompleted is available
                        lastStepCompleted: draft.lastStepCompleted || draft.lastStep || 1
                    };
                });
                setDrafts(processedDrafts);
            } else {
                throw new Error(draftsResponse.error || 'Failed to load drafts');
            }
        } catch (err) {
            console.error('Error loading dashboard data:', err);
            setError(err.message || 'Error loading dashboard data');
        } finally {
            setLoading(false);
        }
    };
    
    // Load data on component mount
    useEffect(() => {
        loadData();
    }, []);
    
    // Handle delete character
    const handleDeleteCharacter = async (characterId, characterName) => {
        if (!window.confirm(`Are you sure you want to delete "${characterName}"? This cannot be undone.`)) {
            return;
        }
        
        try {
            const response = await deleteCharacter(characterId);
            if (response.success) {
                setCharacters(prev => prev.filter(c => c.character_id !== characterId));
                setAlertMessage({
                    type: 'success',
                    message: response.message || 'Character deleted successfully'
                });
            } else {
                throw new Error(response.error || 'Failed to delete character');
            }
        } catch (err) {
            console.error('Error deleting character:', err);
            setAlertMessage({
                type: 'danger',
                message: err.message || 'Error deleting character'
            });
        }
    };
    
    // Handle delete draft
    const handleDeleteDraft = async (draftId, draftName) => {
        if (!window.confirm(`Are you sure you want to delete the draft "${draftName}"? This cannot be undone.`)) {
            return;
        }
        
        try {
            const response = await deleteDraft(draftId);
            if (response.success) {
                setDrafts(prev => prev.filter(d => d.character_id !== draftId));
                setAlertMessage({
                    type: 'success',
                    message: response.message || 'Draft deleted successfully'
                });
            } else {
                throw new Error(response.error || 'Failed to delete draft');
            }
        } catch (err) {
            console.error('Error deleting draft:', err);
            setAlertMessage({
                type: 'danger',
                message: err.message || 'Error deleting draft'
            });
        }
    };
    
    // Handle play button click
    const handlePlayCharacter = (characterId) => {
        window.location.href = `/game/play/${characterId}`;
    };
    
    // Sort characters
    const sortedCharacters = [...characters].sort((a, b) => {
        let valA, valB;
        
        // Handle different field types
        switch (sortField) {
            case 'name':
            case 'race':
            case 'character_class':
            case 'worldName':
            case 'campaignName':
                valA = String(a[sortField] || '').toLowerCase();
                valB = String(b[sortField] || '').toLowerCase();
                break;
            case 'level':
                valA = parseInt(a[sortField] || 0);
                valB = parseInt(b[sortField] || 0);
                break;
            case 'last_played':
                valA = a[sortField] ? new Date(a[sortField]).getTime() : 0;
                valB = b[sortField] ? new Date(b[sortField]).getTime() : 0;
                break;
            default:
                valA = a[sortField];
                valB = b[sortField];
        }
        
        // Apply sort direction
        if (sortDirection === 'asc') {
            return valA > valB ? 1 : -1;
        } else {
            return valA < valB ? 1 : -1;
        }
    });
    
    // Apply filter
    const filteredCharacters = sortedCharacters.filter(character => {
        if (!filter) return true;
        
        const searchFields = [
            character.name || '', 
            character.race || '',
            character.character_class || '',
            character.worldName || '',
            character.campaignName || ''
        ];
        
        const lowerFilter = filter.toLowerCase();
        return searchFields.some(field => String(field).toLowerCase().includes(lowerFilter));
    });
    
    // Handle sort change
    const handleSortChange = (field) => {
        if (field === sortField) {
            // Toggle direction if clicking the same field
            setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
        } else {
            // Set new field and reset direction to desc
            setSortField(field);
            setSortDirection('desc');
        }
    };
    
    // Render sort indicator
    const renderSortIndicator = (field) => {
        if (sortField !== field) return null;
        
        return sortDirection === 'asc' 
            ? <i className="bi bi-arrow-up"></i>
            : <i className="bi bi-arrow-down"></i>;
    };
    
    return (
        <div className="dashboard-container">
            {/* Header */}
            <header className="text-center mb-4">
                <h1 className="display-4 text-light">Your Adventures</h1>
                <p className="lead text-light">Manage your characters and campaigns</p>
            </header>
            
            {/* Alert Message */}
            {alertMessage && (
                <div className={`alert alert-${alertMessage.type} alert-dismissible fade show mb-4`} role="alert">
                    {alertMessage.message}
                    <button 
                        type="button" 
                        className="btn-close" 
                        onClick={() => setAlertMessage(null)} 
                        aria-label="Close"
                    ></button>
                </div>
            )}
            
            {/* Loading State */}
            {loading ? (
                <div className="text-center py-5">
                    <div className="spinner-border text-light" role="status">
                        <span className="visually-hidden">Loading...</span>
                    </div>
                    <p className="text-light mt-2">Loading your adventure data...</p>
                </div>
            ) : error ? (
                <div className="alert alert-danger mb-4" role="alert">
                    {error}
                </div>
            ) : (
                <>
                    {/* New Adventure Card */}
                    <div className="card dashboard-card mb-4">
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
                    
                    {/* Characters Card */}
                    <div className="card dashboard-card mb-4">
                        <div className="card-header bg-dark text-light d-flex justify-content-between align-items-center">
                            <h3 className="mb-0"><i className="bi bi-people me-2"></i>Your Characters</h3>
                            <span className="badge bg-primary">{filteredCharacters.length}</span>
                        </div>
                        <div className="card-body bg-dark text-light p-0">
                            {/* Filter and Sort Controls */}
                            <div className="d-flex justify-content-between align-items-center p-3 border-bottom border-secondary">
                                <div className="input-group" style={{maxWidth: '300px'}}>
                                    <span className="input-group-text bg-dark text-light border-secondary">
                                        <i className="bi bi-search"></i>
                                    </span>
                                    <input 
                                        type="text" 
                                        className="form-control bg-dark text-light border-secondary" 
                                        placeholder="Filter characters..." 
                                        value={filter}
                                        onChange={(e) => setFilter(e.target.value)}
                                    />
                                    {filter && (
                                        <button 
                                            className="btn btn-outline-secondary" 
                                            type="button"
                                            onClick={() => setFilter('')}
                                        >
                                            <i className="bi bi-x"></i>
                                        </button>
                                    )}
                                </div>
                            </div>
                            
                            {filteredCharacters.length > 0 ? (
                                <div className="table-container">
                                    <table className="table table-dark table-hover mb-0 characters-table">
                                        <thead>
                                            <tr>
                                                <th className="sortable" onClick={() => handleSortChange('name')}>
                                                    Name {renderSortIndicator('name')}
                                                </th>
                                                <th className="sortable" onClick={() => handleSortChange('race')}>
                                                    Race {renderSortIndicator('race')}
                                                </th>
                                                <th className="sortable" onClick={() => handleSortChange('character_class')}>
                                                    Class {renderSortIndicator('character_class')}
                                                </th>
                                                <th className="sortable" onClick={() => handleSortChange('level')}>
                                                    Level {renderSortIndicator('level')}
                                                </th>
                                                <th className="sortable" onClick={() => handleSortChange('worldName')}>
                                                    World {renderSortIndicator('worldName')}
                                                </th>
                                                <th className="sortable" onClick={() => handleSortChange('campaignName')}>
                                                    Campaign {renderSortIndicator('campaignName')}
                                                </th>
                                                <th className="sortable" onClick={() => handleSortChange('last_played')}>
                                                    Last Played {renderSortIndicator('last_played')}
                                                </th>
                                                <th>Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {filteredCharacters.map(character => (
                                                 <tr key={character.character_id} data-character-id={character.character_id}>
                                                    <td className="align-middle">{character.name}</td>
                                                    <td className="align-middle">{character.race}</td>
                                                    <td className="align-middle">{character.character_class}</td>
                                                    <td className="align-middle">{character.level}</td>
                                                    <td className="align-middle">{character.worldName || '-'}</td>
                                                    <td className="align-middle">{character.campaignName || '-'}</td>
                                                    <td className="align-middle">{formatDate(character.last_played)}</td>
                                                    <td>
                                                        <div className="d-flex">
                                                            <button 
                                                                className="btn btn-sm btn-success me-2"
                                                                onClick={() => handlePlayCharacter(character.character_id)}
                                                                title="Play character"
                                                            >
                                                                <i className="bi bi-play-fill"></i> Play
                                                            </button>
                                                            <button 
                                                                className="btn btn-sm btn-danger"
                                                                onClick={() => handleDeleteCharacter(character.character_id, character.name)}
                                                                title="Delete character"
                                                            >
                                                                <i className="bi bi-trash"></i>
                                                            </button>
                                                        </div>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            ) : (
                                <div className="p-4 text-center">
                                    <p className="mb-0">
                                        {filter ? 'No characters match your filter.' : 'You haven\'t created any characters yet.'}
                                    </p>
                                </div>
                            )}
                        </div>
                    </div>
                    
                    {/* Drafts Card */}
                    {drafts.length > 0 && (
                        <div className="card dashboard-card mb-4">
                            <div className="card-header bg-dark text-light d-flex justify-content-between align-items-center">
                                <h3 className="mb-0"><i className="bi bi-file-earmark-text me-2"></i>Drafts</h3>
                                <span className="badge bg-warning text-dark">{drafts.length}</span>
                            </div>
                            <div className="card-body bg-dark text-light p-0">
                                <div className="table-container">
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
                                                    <td className="align-middle">
                                                        {draft.lastStepCompleted || 1}/10
                                                    </td>
                                                    <td className="align-middle">
                                                        {formatDate(draft.lastUpdated || draft.updated_at)}
                                                    </td>
                                                    <td>
                                                        <div className="d-flex">
                                                            <Link 
                                                                to={`/characters/create?draft_id=${draft.character_id}`}
                                                                className="btn btn-sm btn-warning text-dark me-2"
                                                                title="Continue draft"
                                                            >
                                                                <i className="bi bi-pencil-fill"></i> Continue
                                                            </Link>
                                                            <button 
                                                                className="btn btn-sm btn-danger"
                                                                onClick={() => handleDeleteDraft(draft.character_id, draft.name || 'Unnamed draft')}
                                                                title="Delete draft"
                                                            >
                                                                <i className="bi bi-trash"></i>
                                                            </button>
                                                        </div>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    )}
                </>
            )}
        </div>
    );
};

export default Dashboard;