// File: frontend/src/components/steps/Step1_WorldSelector.jsx

import React, { useState, useEffect } from 'react';
import './Step1_WorldSelector.css'; // We'll update this CSS file

function Step1_WorldSelector({ characterData, updateCharacterData, nextStep }) {
    const [worlds, setWorlds] = useState([]);
    const [selectedWorldId, setSelectedWorldId] = useState(null);
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
        if (worldId === 'coming_soon_1' || worldId === 'coming_soon_2' || worldId === 'coming_soon_3') {
            return; // Do nothing for coming soon cards
        }
        
        // Toggle selection
        setSelectedWorldId(selectedWorldId === worldId ? null : worldId);
    };

    // Handle confirming the world selection
    const handleConfirmWorld = () => {
        if (!selectedWorldId) return;
        const selectedWorld = worlds.find(w => w.id === selectedWorldId) || 
                            { id: 'forgotten_realms', name: 'Forgotten Realms' };

        console.log(`World confirmed: ${selectedWorld.name}`);
        updateCharacterData({
            worldId: selectedWorld.id,
            worldName: selectedWorld.name,
            campaignId: null, 
            campaignName: null, 
            classId: null
        });
        nextStep(); // Proceed to Step 2
    };

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
            description: 'The most popular D&D setting, a world of sword and sorcery, heroes and villains, light and darkness. From the shining spires of Waterdeep to the monster-infested depths of the Underdark, adventure awaits in every corner of this vast and varied land.',
            image: '/static/images/forgotten_realms.jpg'
        }]),
        // Add three "coming soon" placeholders
        { id: 'coming_soon_1', name: 'Coming Soon', isComingSoon: true },
        { id: 'coming_soon_2', name: 'Coming Soon', isComingSoon: true },
        { id: 'coming_soon_3', name: 'Coming Soon', isComingSoon: true },
    ];

    return (
        <div className="world-selector-fullpage">
            <h2 className="world-selector-title">Choose Your World</h2>
            
            {worldsToShow.map((world) => (
                <div
                    key={world.id}
                    className={`world-card ${selectedWorldId === world.id ? 'expanded' : ''} ${world.isComingSoon ? 'coming-soon' : ''}`}
                    onClick={() => handleWorldClick(world.id)}
                >
                    {/* Card Front (Image and Name) */}
                    <div className="world-image-container">
                        {!world.isComingSoon && world.image && (
                            <img
                                src={world.image.startsWith('http') ? world.image : `/static/${world.image.startsWith('/') ? world.image.substring(1) : world.image}`}
                                alt={world.name}
                                className="world-image"
                            />
                        )}
                        <div className="world-name-overlay">
                            <h3 className="world-name">{world.name}</h3>
                        </div>
                    </div>
                    
                    {/* Card Details (Only visible when expanded) */}
                    {!world.isComingSoon && (
                        <div className="world-card-details">
                            <div className="world-description-content">
                                <h3 className="expanded-world-name">{world.name}</h3>
                                <p className="world-description">{world.description}</p>
                                <button 
                                    className="btn btn-primary confirm-world-btn"
                                    onClick={(e) => {
                                        e.stopPropagation(); // Prevent toggling the card
                                        handleConfirmWorld();
                                    }}
                                >
                                    Begin Adventure
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            ))}
        </div>
    );
}

export default Step1_WorldSelector;