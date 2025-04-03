// File: frontend/src/components/steps/Step1_WorldSelector.jsx

import React, { useState, useEffect } from 'react';

// Props will be passed from CharacterCreator:
// - characterData (read-only access to current state)
// - updateCharacterData (function to update parent state)
// - nextStep (function to go to the next step)
function Step1_WorldSelector({ characterData, updateCharacterData, nextStep }) {
    const [worlds, setWorlds] = useState([]);
    const [selectedWorldId, setSelectedWorldId] = useState(characterData.worldId || null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);

    // Fetch worlds from the backend API when the component mounts
    useEffect(() => {
        setIsLoading(true);
        setError(null);
        console.log("Fetching worlds from /api/worlds...");
        fetch('/api/worlds') // Relative URL assumes React dev server proxies or same origin
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log("Worlds fetched:", data);
                if (data.success && Array.isArray(data.worlds)) {
                    setWorlds(data.worlds);
                } else {
                    throw new Error(data.error || 'Invalid data format received for worlds.');
                }
                setIsLoading(false);
            })
            .catch(err => {
                console.error("Failed to fetch worlds:", err);
                setError(`Failed to load worlds: ${err.message}. Make sure the Flask server is running and the API endpoint is correct.`);
                setIsLoading(false);
            });
    }, []); // Empty dependency array means this runs once on mount

    // Handle world selection
    const handleSelectWorld = (world) => {
        console.log("World selected:", world);
        setSelectedWorldId(world.id);
        // Update the parent component's state
        updateCharacterData({
            worldId: world.id,
            worldName: world.name
            // Reset subsequent dependent choices if needed when world changes
            // campaignId: null, classId: null, raceId: null, etc.
        });
    };

    return (
        <div className="step-world-selector">
            <h3 className="mb-4 text-light text-center">Choose Your World</h3>

            {isLoading && <p className="text-center text-light">Loading worlds...</p>}
            {error && <div className="alert alert-danger" role="alert">{error}</div>}

            {!isLoading && !error && (
                <div className="row g-3">
                    {worlds.length === 0 && !isLoading && (
                        <p className="text-center text-light">No worlds found. Please check the backend data.</p>
                    )}
                    {worlds.map((world) => (
                        <div className="col-md-6 col-lg-4" key={world.id}>
                            {/* Use the existing CSS classes */}
                            <div
                                className={`card selection-card h-100 ${selectedWorldId === world.id ? 'selected' : ''}`}
                                onClick={() => handleSelectWorld(world)}
                                style={{ cursor: 'pointer' }} // Ensure pointer cursor
                            >
                                <div className="card-body d-flex flex-column">
                                    {/* Optional: Add image if available */}
                                    {world.image && (
                                         <img src={world.image} alt={world.name} className="card-img-top mb-2" style={{maxHeight: '150px', objectFit: 'cover'}}/>
                                    )}
                                    <h5 className="card-title">{world.name}</h5>
                                    <p className="card-text small flex-grow-1">{world.description}</p>
                                </div>
                                <div className="card-footer">
                                    <div className="selected-indicator">
                                        <i className="bi bi-check-circle-fill"></i> Selected
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Navigation */}
            <div className="d-flex justify-content-end mt-4">
                 {/* No "Back" button on the first step */}
                <button
                    type="button"
                    className="btn btn-primary btn-lg"
                    onClick={nextStep}
                    disabled={!selectedWorldId || isLoading} // Disable until a world is selected
                >
                    Next: Choose Campaign &raquo;
                </button>
            </div>
        </div>
    );
}

export default Step1_WorldSelector;