// File: frontend/src/components/steps/Step1_WorldSelector.jsx

import React, { useState, useEffect } from 'react';
import './Step1_WorldSelector.css'; // We'll create this CSS file next

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
                    console.error('Failed fetch for: /characters/api/worlds - Status: ${response.status}');
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

    // Handle clicking on a world grid item
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
            campaignId: null, campaignName: null, classId: null, etc: null 
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

    // Prepare grid items (max 16 for 4x4)
    const gridItems = [];
    const totalGridSlots = 16;
    const availableWorlds = worlds.slice(0, 1); // Only show first world for now
    
    // Add available worlds
    availableWorlds.forEach(world => {
        gridItems.push({ type: 'world', data: world });
    });

    // Add "Coming Soon" placeholders
    const comingSoonCount = totalGridSlots - gridItems.length;
    for (let i = 0; i < comingSoonCount; i++) {
        gridItems.push({ type: 'coming_soon', id: `cs-${i}` });
    }


    return (
        <div className={`step-world-selector ${enlargedWorldId ? 'detail-view-active' : ''}`}>
            <h3 className="mb-4 text-light text-center">Choose Your World</h3>

            {/* The Grid */}
            <div className="world-grid">
                {gridItems.map((item, index) => {
                    if (item.type === 'world') {
                        const world = item.data;
                        return (
                            <div
                                key={world.id}
                                className={`world-item card selection-card`} // Reuse selection-card style
                                onClick={() => handleWorldClick(world.id)}
                                role="button"
                                tabIndex={0}
                                onKeyPress={(e) => (e.key === 'Enter' || e.key === ' ') && handleWorldClick(world.id)}
                            >
                                {world.image && <img src={world.image.startsWith('http') ? world.image : `/static/${world.image.startsWith('/') ? world.image.substring(1) : world.image}`} alt={world.name} className="world-item-thumbnail"/>}
                                <div className="world-item-name">{world.name}</div>
                            </div>
                        );
                    } else { // Coming Soon placeholder
                        return (
                            <div key={item.id} className="world-item coming-soon card">
                                {/* <img src="/static/images/placeholder.png" alt="Coming Soon" className="world-item-thumbnail placeholder"/> */}
                                <div className="world-item-name">Coming Soon</div>
                            </div>
                        );
                    }
                })}
            </div>

            {/* Enlarged Detail View (Conditionally Rendered) */}
            {enlargedWorldData && (
                // Use a modal-like overlay approach
                <div className="world-detail-overlay" onClick={handleCloseEnlarged}>
                    <div className="world-detail-content card" onClick={(e) => e.stopPropagation()}> {/* Stop clicks inside from closing it */}
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
                            <p>{enlargedWorldData.description}</p>
                            <button 
                                className="btn btn-primary btn-lg confirm-button"
                                onClick={handleConfirmWorld}
                            >
                                Confirm World
                            </button>
                        </div>
                    </div>
                </div>
            )}

             {/* Navigation Buttons - Only show if detail view is NOT active */}
             {!enlargedWorldId && (
                 <div className="d-flex justify-content-end mt-4" style={{ visibility: 'hidden' }}> 
                    {/* Keep for spacing maybe, but disabled */}
                    <button className="btn btn-primary btn-lg">Next</button>
                 </div>
             )}
        </div>
    );
}

export default Step1_WorldSelector;