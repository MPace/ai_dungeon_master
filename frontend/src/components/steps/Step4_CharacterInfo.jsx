// File: frontend/src/components/steps/Step4_CharacterInfo.jsx - Updated with horizontal scrolling

import React, { useState, useEffect, useCallback, useRef } from 'react';
import './Step4_CharacterInfo.css';

function Step4_CharacterInfo({ characterData, updateCharacterData, nextStep, prevStep }) {
    const [name, setName] = useState(characterData.characterName || '');
    const [gender, setGender] = useState(characterData.gender || 'male');
    const [races, setRaces] = useState([]);
    const [backgrounds, setBackgrounds] = useState([]);
    const [selectedRaceId, setSelectedRaceId] = useState(characterData.raceId || null);
    const [selectedRace, setSelectedRace] = useState(null);
    const [selectedSubraceId, setSelectedSubraceId] = useState(characterData.subraceId || null);
    const [selectedBackgroundId, setSelectedBackgroundId] = useState(characterData.backgroundId || null);
    const [selectedBackground, setSelectedBackground] = useState(null);
    const [isRaceModalOpen, setIsRaceModalOpen] = useState(false);
    const [isBackgroundModalOpen, setIsBackgroundModalOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    
    // Refs for modals
    const raceModalRef = useRef(null);
    const backgroundModalRef = useRef(null);
    // New refs for horizontal scrolling
    const raceGridRef = useRef(null);
    const backgroundGridRef = useRef(null);

    // Fetch data for the selected world
    useEffect(() => {
        if (!characterData.worldId) {
            setError("No world selected. Please go back to Step 1.");
            setIsLoading(false);
            return;
        }

        setIsLoading(true);
        setError(null);
        
        // Fetch data from the API (using the world ID to filter allowed options)
        fetch(`/characters/api/creation-data/${characterData.worldId}`)
            .then(response => {
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                return response.json();
            })
            .then(data => {
                if (data.success && data.data) {
                    console.log("Character creation data:", data.data);
                    
                    // Set races and backgrounds
                    if (Array.isArray(data.data.races)) {
                        setRaces(data.data.races);
                        
                        // If we already have a selected race, find it in the new data
                        if (characterData.raceId) {
                            const race = data.data.races.find(r => r.id === characterData.raceId);
                            setSelectedRace(race || null);
                        }
                    }
                    
                    if (Array.isArray(data.data.backgrounds)) {
                        setBackgrounds(data.data.backgrounds);
                        
                        // If we already have a selected background, find it in the new data
                        if (characterData.backgroundId) {
                            const background = data.data.backgrounds.find(b => b.id === characterData.backgroundId);
                            setSelectedBackground(background || null);
                        }
                    }
                    
                    setIsLoading(false);
                } else {
                    throw new Error(data.error || 'Invalid data format.');
                }
            })
            .catch(err => {
                console.error("Step4: Failed to fetch data:", err);
                setError(`Failed to load data: ${err.message}. Check your connection or try again later.`);
                setIsLoading(false);
            });
    }, [characterData.worldId, characterData.raceId, characterData.backgroundId]);

    // Helper to get the full image URL
    const getImageUrl = useCallback((imagePath) => {
        if (!imagePath) return null;
        
        // If it's already a full URL (http or https), use it directly
        if (imagePath.startsWith('http://') || imagePath.startsWith('https://')) {
            return imagePath;
        }
        
        // Handle relative paths by adding the static prefix
        return `/static/build/${imagePath.startsWith('/') ? imagePath.substring(1) : imagePath}`;
    }, []);

    // Handler for horizontal scrolling
    const handleScroll = (direction, containerRef) => {
        if (!containerRef.current) return;
        
        const scrollAmount = 300; // Adjust as needed
        const currentScroll = containerRef.current.scrollLeft;
        
        if (direction === 'left') {
            containerRef.current.scrollTo({
                left: currentScroll - scrollAmount,
                behavior: 'smooth'
            });
        } else {
            containerRef.current.scrollTo({
                left: currentScroll + scrollAmount,
                behavior: 'smooth'
            });
        }
    };

    // Handler when a race card is clicked
    const handleRaceSelect = useCallback((race) => {
        console.log("Race selected:", race.name);
        setSelectedRace(race);
        setSelectedRaceId(race.id);
        
        // Reset subrace if changing races
        setSelectedSubraceId(null);
        
        // Open modal
        setIsRaceModalOpen(true);
        
        // Add a slight delay before adding the active class for animation
        setTimeout(() => {
            if (raceModalRef.current) {
                raceModalRef.current.classList.add('active');
            }
        }, 10);
    }, []);

    // Handler when a background card is clicked
    const handleBackgroundSelect = useCallback((background) => {
        console.log("Background selected:", background.name);
        setSelectedBackground(background);
        setSelectedBackgroundId(background.id);
        
        // Open modal
        setIsBackgroundModalOpen(true);
        
        // Add a slight delay before adding the active class for animation
        setTimeout(() => {
            if (backgroundModalRef.current) {
                backgroundModalRef.current.classList.add('active');
            }
        }, 10);
    }, []);

    // Handler for selecting a subrace
    const handleSubraceSelect = useCallback((subraceId) => {
        console.log("Subrace selected:", subraceId);
        setSelectedSubraceId(subraceId);
    }, []);

    // Handler to close the race modal
    const closeRaceModal = useCallback(() => {
        if (raceModalRef.current) {
            raceModalRef.current.classList.remove('active');
            
            // Wait for animation to complete before removing modal
            setTimeout(() => {
                setIsRaceModalOpen(false);
            }, 400);
        } else {
            setIsRaceModalOpen(false);
        }
    }, []);

    // Handler to close the background modal
    const closeBackgroundModal = useCallback(() => {
        if (backgroundModalRef.current) {
            backgroundModalRef.current.classList.remove('active');
            
            // Wait for animation to complete before removing modal
            setTimeout(() => {
                setIsBackgroundModalOpen(false);
            }, 400);
        } else {
            setIsBackgroundModalOpen(false);
        }
    }, []);

    // Handler for the final confirmation button
    const handleConfirm = () => {
        // Validate input
        if (!name.trim()) {
            alert("Please enter a character name.");
            return;
        }
        
        if (!selectedRaceId) {
            alert("Please select a race.");
            return;
        }
        
        if (!selectedBackgroundId) {
            alert("Please select a background.");
            return;
        }
        
        // If race has subraces but none selected, show error
        if (selectedRace && selectedRace.hasSubraces && !selectedSubraceId) {
            alert("Please select a subrace.");
            return;
        }
        
        console.log("Character info confirmed");
        
        const completeRaceData = selectedRace;

        // Update character data
        updateCharacterData({
            characterName: name,
            gender: gender,
            raceId: selectedRaceId,
            raceName: selectedRace?.name || '',
            subraceId: selectedSubraceId,
            subraceName: selectedSubraceId ? 
                selectedRace?.subraces?.find(sr => sr.id === selectedSubraceId)?.name || '' : '',
            backgroundId: selectedBackgroundId,
            backgroundName: selectedBackground?.name || '',
            raceData: completeRaceData
        });
        
        // Move to next step
        nextStep();
    };

    // --- Render Logic ---
    if (isLoading) {
        return (
            <div className="loading-container">
                <div className="spinner-border" role="status"></div>
                <div>Loading Character Options...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="error-container">
                <p>{error}</p>
                <button className="back-button" onClick={prevStep}>
                    <i className="bi bi-arrow-left"></i> Go Back
                </button>
            </div>
        );
    }

    return (
        <div className="step4-outer-container">
            {/* Title */}
            <h2 className="step4-title">Character Information</h2>

            {/* Name and Gender section */}
            <div className="character-basics-container">
                <div className="name-container">
                    <label htmlFor="character-name">Character Name</label>
                    <input 
                        type="text" 
                        id="character-name" 
                        className="character-name-input" 
                        value={name} 
                        onChange={(e) => setName(e.target.value)}
                        placeholder="Enter character name"
                    />
                </div>
                
                <div className="gender-container">
                    <label>Gender</label>
                    <div className="gender-toggle">
                        <button 
                            className={`gender-button ${gender === 'male' ? 'active' : ''}`}
                            onClick={() => setGender('male')}
                        >
                            <i className="bi bi-gender-male"></i> Male
                        </button>
                        <button 
                            className={`gender-button ${gender === 'female' ? 'active' : ''}`}
                            onClick={() => setGender('female')}
                        >
                            <i className="bi bi-gender-female"></i> Female
                        </button>
                    </div>
                </div>
            </div>

            {/* Race and Background selection containers */}
            <div className="selection-containers">
                {/* Race selection */}
                <div className="race-selection-container">
                    <h3 className="section-title">Race</h3>
                    
                    {selectedRace ? (
                        <div className="selected-item-container">
                            <div className="selected-item">
                                <div className="selected-item-image">
                                    {selectedRace.image ? (
                                        <img src={getImageUrl(selectedRace.image)} alt={selectedRace.name} />
                                    ) : (
                                        <div className="placeholder-image">
                                            <i className="bi bi-person"></i>
                                        </div>
                                    )}
                                </div>
                                <div className="selected-item-details">
                                    <h4>{selectedRace.name}</h4>
                                    {selectedSubraceId && selectedRace.subraces?.length > 0 && (
                                        <h5>{selectedRace.subraces.find(sr => sr.id === selectedSubraceId)?.name || 'Subrace'}</h5>
                                    )}
                                    <p>{selectedRace.shortDescription}</p>
                                </div>
                                <button className="change-button" onClick={() => setSelectedRace(null)}>
                                    Change
                                </button>
                            </div>
                        </div>
                    ) : (
                        <div>
                            <div className="race-grid" ref={raceGridRef}>
                                {races.map((race) => (
                                    <div 
                                        key={race.id} 
                                        className="race-card" 
                                        onClick={() => handleRaceSelect(race)}
                                    >
                                        <div className="race-image-container">
                                            {race.image ? (
                                                <img src={getImageUrl(race.image)} alt={race.name} className="race-image" />
                                            ) : (
                                                <div className="placeholder-image">
                                                    <i className="bi bi-person"></i>
                                                </div>
                                            )}
                                        </div>
                                        <div className="race-card-content">
                                            <h4 className="race-name">{race.name}</h4>
                                            <p className="race-description">{race.shortDescription}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                            <div className="scroll-nav-buttons">
                                <button 
                                    className="scroll-button" 
                                    onClick={() => handleScroll('left', raceGridRef)}
                                    aria-label="Scroll left"
                                >
                                    <i className="bi bi-chevron-left"></i>
                                </button>
                                <button 
                                    className="scroll-button" 
                                    onClick={() => handleScroll('right', raceGridRef)}
                                    aria-label="Scroll right"
                                >
                                    <i className="bi bi-chevron-right"></i>
                                </button>
                            </div>
                        </div>
                    )}
                </div>
                
                {/* Background selection */}
                <div className="background-selection-container">
                    <h3 className="section-title">Background</h3>
                    
                    {selectedBackground ? (
                        <div className="selected-item-container">
                            <div className="selected-item">
                                <div className="selected-item-image">
                                    {selectedBackground.image ? (
                                        <img src={getImageUrl(selectedBackground.image)} alt={selectedBackground.name} />
                                    ) : (
                                        <div className="placeholder-image">
                                            <i className="bi bi-book"></i>
                                        </div>
                                    )}
                                </div>
                                <div className="selected-item-details">
                                    <h4>{selectedBackground.name}</h4>
                                    <p>{selectedBackground.shortDescription}</p>
                                </div>
                                <button className="change-button" onClick={() => setSelectedBackground(null)}>
                                    Change
                                </button>
                            </div>
                        </div>
                    ) : (
                        <div>
                            <div className="background-grid" ref={backgroundGridRef}>
                                {backgrounds.map((background) => (
                                    <div 
                                        key={background.id} 
                                        className="background-card" 
                                        onClick={() => handleBackgroundSelect(background)}
                                    >
                                        <div className="background-image-container">
                                            {background.image ? (
                                                <img src={getImageUrl(background.image)} alt={background.name} className="background-image" />
                                            ) : (
                                                <div className="placeholder-image">
                                                    <i className="bi bi-book"></i>
                                                </div>
                                            )}
                                        </div>
                                        <div className="background-card-content">
                                            <h4 className="background-name">{background.name}</h4>
                                            <p className="background-description">{background.shortDescription}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                            <div className="scroll-nav-buttons">
                                <button 
                                    className="scroll-button" 
                                    onClick={() => handleScroll('left', backgroundGridRef)}
                                    aria-label="Scroll left"
                                >
                                    <i className="bi bi-chevron-left"></i>
                                </button>
                                <button 
                                    className="scroll-button" 
                                    onClick={() => handleScroll('right', backgroundGridRef)}
                                    aria-label="Scroll right"
                                >
                                    <i className="bi bi-chevron-right"></i>
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Race Details Modal */}
            {isRaceModalOpen && selectedRace && (
                <div className="modal-overlay" ref={raceModalRef} onClick={closeRaceModal}>
                    <div className="race-modal" onClick={(e) => e.stopPropagation()}>
                        <button className="modal-close-btn" onClick={closeRaceModal}>×</button>
                        
                        {/* Race Image */}
                        {selectedRace.image && (
                            <div className="modal-image-container">
                                <img 
                                    src={getImageUrl(selectedRace.image)} 
                                    alt={selectedRace.name} 
                                    className="modal-image"
                                />
                            </div>
                        )}
                        
                        {/* Modal Content */}
                        <div className="modal-content">
                            <h2 className="modal-title">{selectedRace.name}</h2>
                            <p className="modal-description">{selectedRace.description}</p>
                            
                            {/* Race Traits */}
                            <div className="race-traits-section">
                                <h3>Racial Traits</h3>
                                <div className="traits-grid">
                                    {selectedRace.traits?.map((trait, index) => (
                                        <div key={index} className="trait-card">
                                            <h4 className="trait-title">{trait.name}</h4>
                                            <p className="trait-description">{trait.description}</p>
                                        </div>
                                    ))}
                                </div>
                            </div>
                            
                            {/* Ability Score Adjustments */}
                            {selectedRace.abilityScoreAdjustments && (
                                <div className="ability-adjustments-section">
                                    <h3>Ability Score Adjustments</h3>
                                    <div className="ability-adjustments-grid">
                                        {Object.entries(selectedRace.abilityScoreAdjustments).map(([ability, adjustment]) => (
                                            <div key={ability} className="ability-adjustment">
                                                <span className="ability-name">{ability.charAt(0).toUpperCase() + ability.slice(1)}</span>
                                                <span className="ability-value">+{adjustment}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                            
                            {/* Subrace Selection if applicable */}
                            {selectedRace.hasSubraces && selectedRace.subraces?.length > 0 && (
                                <div className="subrace-section">
                                    <h3>Choose a Subrace</h3>
                                    <div className="subrace-grid">
                                        {selectedRace.subraces.map((subrace) => (
                                            <div 
                                                key={subrace.id} 
                                                className={`subrace-card ${selectedSubraceId === subrace.id ? 'selected' : ''}`}
                                                onClick={() => handleSubraceSelect(subrace.id)}
                                            >
                                                <h4 className="subrace-name">{subrace.name}</h4>
                                                <p className="subrace-description">{subrace.description}</p>
                                                
                                                {/* Subrace Ability Adjustments */}
                                                {subrace.abilityScoreAdjustments && (
                                                    <div className="subrace-adjustments">
                                                        <h5>Ability Adjustments</h5>
                                                        <div className="subrace-adjustments-list">
                                                            {Object.entries(subrace.abilityScoreAdjustments).map(([ability, adjustment]) => (
                                                                <span key={ability} className="subrace-adjustment">
                                                                    {ability.charAt(0).toUpperCase() + ability.slice(1)} +{adjustment}
                                                                </span>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}
                                                
                                                {/* Subrace Traits */}
                                                {subrace.traits?.length > 0 && (
                                                    <div className="subrace-traits">
                                                        <h5>Traits</h5>
                                                        <ul className="subrace-traits-list">
                                                            {subrace.traits.map((trait, index) => (
                                                                <li key={index}>
                                                                    <strong>{trait.name}:</strong> {trait.description}
                                                                </li>
                                                            ))}
                                                        </ul>
                                                    </div>
                                                )}
                                                
                                                <div className="subrace-selected-indicator">
                                                    <i className="bi bi-check-circle-fill"></i> Selected
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                            
                            {/* Confirm Button */}
                            <div className="modal-confirm-container">
                                <button 
                                    className="modal-confirm-btn"
                                    onClick={closeRaceModal}
                                    disabled={selectedRace.hasSubraces && !selectedSubraceId}
                                >
                                    Confirm {selectedRace.name} 
                                    {selectedSubraceId && selectedRace.subraces?.length > 0 ? 
                                        ` (${selectedRace.subraces.find(sr => sr.id === selectedSubraceId)?.name})` : ''}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Background Details Modal */}
            {isBackgroundModalOpen && selectedBackground && (
                <div className="modal-overlay" ref={backgroundModalRef} onClick={closeBackgroundModal}>
                    <div className="background-modal" onClick={(e) => e.stopPropagation()}>
                        <button className="modal-close-btn" onClick={closeBackgroundModal}>×</button>
                        
                        {/* Background Image */}
                        {selectedBackground.image && (
                            <div className="modal-image-container">
                                <img 
                                    src={getImageUrl(selectedBackground.image)} 
                                    alt={selectedBackground.name} 
                                    className="modal-image"
                                />
                            </div>
                        )}
                        
                        {/* Modal Content */}
                        <div className="modal-content">
                            <h2 className="modal-title">{selectedBackground.name}</h2>
                            <p className="modal-description">{selectedBackground.description}</p>
                            
                            {/* Background Feature */}
                            {selectedBackground.feature && (
                                <div className="background-feature-section">
                                    <h3>Feature: {selectedBackground.feature.name}</h3>
                                    <p className="feature-description">{selectedBackground.feature.description}</p>
                                </div>
                            )}
                            
                            {/* Proficiencies */}
                            <div className="proficiencies-section">
                                <h3>Proficiencies</h3>
                                <div className="proficiencies-grid">
                                    {/* Skill Proficiencies */}
                                    <div className="proficiency-card">
                                        <h4>Skill Proficiencies</h4>
                                        <ul className="proficiency-list">
                                            {selectedBackground.skillProficiencies?.map((skill, index) => (
                                                <li key={index}>{skill}</li>
                                            ))}
                                        </ul>
                                    </div>
                                    
                                    {/* Languages */}
                                    {selectedBackground.languages && (
                                        <div className="proficiency-card">
                                            <h4>Languages</h4>
                                            <p>{selectedBackground.languages.description}</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                            
                            {/* Equipment */}
                            {selectedBackground.startingEquipment && (
                                <div className="equipment-section">
                                    <h3>Starting Equipment</h3>
                                    <ul className="equipment-list">
                                        {selectedBackground.startingEquipment.map((item, index) => (
                                            <li key={index}>{item}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                            
                            {/* Suggested Characteristics */}
                            {selectedBackground.suggestedCharacteristics && (
                                <div className="characteristics-section">
                                    <h3>Suggested Characteristics</h3>
                                    <div className="characteristics-tabs">
                                        <div className="characteristic-tab">
                                            <h4>Personality Traits</h4>
                                            <ul className="characteristic-list">
                                                {selectedBackground.suggestedCharacteristics.personalityTraits?.map((trait, index) => (
                                                    <li key={index}>{trait}</li>
                                                ))}
                                            </ul>
                                        </div>
                                        
                                        <div className="characteristic-tab">
                                            <h4>Ideals</h4>
                                            <ul className="characteristic-list">
                                                {selectedBackground.suggestedCharacteristics.ideals?.map((ideal, index) => (
                                                    <li key={index}>{ideal}</li>
                                                ))}
                                            </ul>
                                        </div>
                                        
                                        <div className="characteristic-tab">
                                            <h4>Bonds</h4>
                                            <ul className="characteristic-list">
                                                {selectedBackground.suggestedCharacteristics.bonds?.map((bond, index) => (
                                                    <li key={index}>{bond}</li>
                                                ))}
                                            </ul>
                                        </div>
                                        
                                        <div className="characteristic-tab">
                                            <h4>Flaws</h4>
                                            <ul className="characteristic-list">
                                                {selectedBackground.suggestedCharacteristics.flaws?.map((flaw, index) => (
                                                    <li key={index}>{flaw}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    </div>
                                </div>
                            )}
                            
                            {/* Confirm Button */}
                            <div className="modal-confirm-container">
                                <button 
                                    className="modal-confirm-btn"
                                    onClick={closeBackgroundModal}
                                >
                                    Confirm {selectedBackground.name}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Navigation Buttons */}
            <div className="step4-navigation">
                <button className="back-button" onClick={prevStep}>
                    <i className="bi bi-arrow-left"></i> Back to Class Selection
                </button>
                
                <button 
                    className={`continue-button ${name && selectedRaceId && selectedBackgroundId && (!selectedRace?.hasSubraces || selectedSubraceId) ? 'active' : ''}`}
                    onClick={handleConfirm}
                    disabled={!name || !selectedRaceId || !selectedBackgroundId || (selectedRace?.hasSubraces && !selectedSubraceId)}
                >
                    Continue to Abilities <i className="bi bi-arrow-right"></i>
                </button>
            </div>
        </div>
    );
}

export default Step4_CharacterInfo;