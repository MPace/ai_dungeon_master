// File: frontend/src/components/steps/Step1_WorldSelector.jsx

import React, { useState, useEffect } from 'react';
import './Step1_WorldSelector.css'; // We'll update this CSS file

// Props passed from CharacterCreator: characterData, updateCharacterData, nextStep
function Step1_WorldSelector({ characterData, updateCharacterData, nextStep }) {
    const [worlds, setWorlds] = useState([]);
    // State to track which world's detail view is open ('null' means none)
    const [enlargedWorldId, setEnlargedWorldId] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);

    // Fetch worlds data on component mount
    useEffect(() => {
        setIsLoading(true);
        setError(null);
        console.log("Step1: Fetching worlds from /characters/api/worlds...");
        fetch('/characters/api/worlds')
            .then(response => {
                if (!response.ok) {
                    console.error(`Failed fetch for: /characters/api/worlds - Status: ${response.status}`);
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log("Step1: Worlds fetched:", data);
                if (data.success && Array.isArray(data.worlds)) {
                    setWorlds(data.worlds);
                } else {
                    throw new Error(data.error || 'Invalid data format for worlds.');
                }
                setIsLoading(false);
            })
            .catch(err => {
                console.error("Step1: Failed to fetch worlds:", err);
                setError(`Failed to load worlds: ${err.message}. Check API endpoint.`);
                setIsLoading(false);
            });
    }, []);

    // Handle clicking on a world card
    const handleWorldClick = (worldId) => {
        if (worldId === 'coming_soon') return; // Do nothing for coming soon cards
        console.log(`World clicked: ${worldId}`);
        setEnlargedWorldId(worldId); // Set state to show enlarged view
    };

    // Handle closing the enlarged view
    const handleCloseEnlarged = (e) => {
        // Prevent click from propagating to the background if needed
        if (e) e.stopPropagation(); 
        console.log('Closing enlarged view');
        setEnlargedWorldId(null);
    };

    // Handle confirming the world selection
    const handleConfirmWorld = () => {
        if (!enlargedWorldId) return;
        const selectedWorld = worlds.find(w => w.id === enlargedWorldId);
        if (!selectedWorld) return;

        console.log(`World confirmed: ${selectedWorld.name}`);
        updateCharacterData({
            worldId: selectedWorld.id,
            worldName: selectedWorld.name,
            // Reset potentially dependent data
            campaignId: null, campaignName: null, classId: null
        });
        nextStep(); // Proceed to Step 2
    };

    // Find the world data for the currently enlarged world
    const enlargedWorldData = enlargedWorldId ? worlds.find(w => w.id === enlargedWorldId) : null;

    // --- Render Logic ---

    if (isLoading) {
        return <div className="text-center p-5 text-light">Loading Worlds... <div className="spinner-border spinner-border-sm" role="status"></div></div>;
    }

    if (error) {
        return <div className="alert alert-danger">{error}</div>;
    }
    
    // Create the world cards - one real world and three "coming soon"
    const worldsToShow = [
        // Take the first real world if available, otherwise create a placeholder
        ...(worlds.length > 0 ? [worlds[0]] : [{
            id: 'forgotten_realms',
            name: 'Forgotten Realms',
            description: 'The most popular D&D setting, a world of sword and sorcery, heroes and villains, light and darkness.',
            image: '/static/images/forgotten_realms.jpg'
        }]),
        // Add three "coming soon" placeholders
        { id: 'coming_soon_1', name: 'Coming Soon', description: 'New world coming soon!', isComingSoon: true },
        { id: 'coming_soon_2', name: 'Coming Soon', description: 'New world coming soon!', isComingSoon: true },
        { id: 'coming_soon_3', name: 'Coming Soon', description: 'New world coming soon!', isComingSoon: true },
    ];

    return (
        <div className={`step-world-selector ${enlargedWorldId ? 'detail-view-active' : ''}`}>
            <h3 className="mb-4 text-light text-center">Choose Your World</h3>
            
            {/* Horizontal scrollable container for world cards */}
            <div className="world-scroll-container">
                <div className="world-cards-wrapper">
                    {worldsToShow.map((world) => (
                        <div
                            key={world.id}
                            className={`world-card selection-card ${world.isComingSoon ? 'coming-soon' : ''}`}
                            onClick={() => !world.isComingSoon && handleWorldClick(world.id)}
                            role="button"
                            tabIndex={0}
                            onKeyPress={(e) => (!world.isComingSoon && (e.key === 'Enter' || e.key === ' ')) && handleWorldClick(world.id)}
                        >
                            <div className="card-body">
                                <h5 className="card-title">{world.name}</h5>
                                <p className="card-text small">{world.description || 'An exciting world awaits adventurers.'}</p>
                                
                                {world.image && !world.isComingSoon && (
                                    <div className="world-image-container">
                                        <img
                                            src={world.image.startsWith('http') ? world.image : `/static/${world.image.startsWith('/') ? world.image.substring(1) : world.image}`}
                                            alt={world.name}
                                            className="world-image"
                                        />
                                    </div>
                                )}
                                
                                {!world.isComingSoon && (
                                    <div className="card-footer">
                                        <div className="selection-indicator">
                                            <i className="bi bi-check-circle-fill"></i> Select
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Enlarged Detail View (Conditionally Rendered) */}
            {enlargedWorldData && (
                <div className="world-detail-overlay" onClick={handleCloseEnlarged}>
                    <div className="world-detail-content card" onClick={(e) => e.stopPropagation()}>
                        <button className="btn-close btn-close-white close-button" onClick={handleCloseEnlarged} aria-label="Close"></button>
                        
                        {enlargedWorldData.image && (
                            <img 
                                src={enlargedWorldData.image.startsWith('http') ? enlargedWorldData.image : `/static/${enlargedWorldData.image.startsWith('/') ? enlargedWorldData.image.substring(1) : enlargedWorldData.image}`} 
                                alt={enlargedWorldData.name} 
                                className="world-detail-image"
                            />
                        )}
                        
                        <div className="world-detail-body">
                            <h3>{enlargedWorldData.name}</h3>
                            <p>{enlargedWorldData.description || 'An exciting world awaits adventurers.'}</p>
                            <button 
                                className="btn btn-primary btn-lg confirm-button"
                                onClick={handleConfirmWorld}
                            >
                                Begin Adventure
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Navigation Buttons - Only show if detail view is NOT active */}
            {!enlargedWorldId && (
                <div className="d-flex justify-content-end mt-4" style={{ visibility: 'hidden' }}> 
                    {/* Keep for spacing, but hidden */}
                    <button className="btn btn-primary btn-lg">Next</button>
                </div>
            )}
        </div>
    );
}

export default Step1_WorldSelector;