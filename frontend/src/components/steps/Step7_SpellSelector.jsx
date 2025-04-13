// File: frontend/src/components/steps/Step7_SpellSelector.jsx

import React, { useState, useEffect, useCallback, useRef } from 'react';
import './Step7_SpellSelector.css';

function Step7_SpellSelector({ characterData, updateCharacterData, nextStep, prevStep }) {
    const [availableSpells, setAvailableSpells] = useState({
        cantrips: [],
        level1: []
    });
    const [selectedCantrips, setSelectedCantrips] = useState([]);
    const [selectedSpells, setSelectedSpells] = useState([]);
    const [maxCantrips, setMaxCantrips] = useState(0);
    const [maxSpells, setMaxSpells] = useState(0);
    const [showSpellDetails, setShowSpellDetails] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState('cantrips');
    const [showExtraSpells, setShowExtraSpells] = useState(false);
    
    // Ref for spell details modal
    const spellDetailsRef = useRef(null);

    // Determine if the class can cast spells
    const hasSpellcasting = useCallback(() => {
        const spellcastingClasses = ['wizard', 'sorcerer', 'bard', 'cleric', 'druid', 'paladin', 'ranger', 'warlock'];
        return spellcastingClasses.includes(characterData.classId);
    }, [characterData.classId]);

    // Determine if character has racial spellcasting (e.g., High Elf cantrip)
    const hasRacialSpellcasting = useCallback(() => {
        if (characterData.raceData && characterData.subraceId) {
            const subrace = characterData.raceData.subraces?.find(sr => sr.id === characterData.subraceId);
            if (subrace) {
                const traits = subrace.traits || [];
                return traits.some(trait => trait.name === 'Cantrip' || trait.name.includes('magic'));
            }
        }
        return false;
    }, [characterData.raceData, characterData.subraceId]);

    // Calculate spell slots based on class
    useEffect(() => {
        if (!hasSpellcasting() && !hasRacialSpellcasting()) {
            // If character can't cast spells, skip loading
            setIsLoading(false);
            return;
        }

        // Get spell slots based on class
        if (hasSpellcasting()) {
            switch (characterData.classId) {
                case 'wizard':
                case 'cleric':
                case 'druid':
                case 'bard':
                    setMaxCantrips(3);
                    setMaxSpells(6); // Typically Intelligence/Wisdom/Charisma mod + level (assumed to be ~3 at level 1)
                    break;
                case 'sorcerer':
                    setMaxCantrips(4);
                    setMaxSpells(2);
                    break;
                case 'warlock':
                    setMaxCantrips(2);
                    setMaxSpells(2);
                    break;
                case 'paladin':
                case 'ranger':
                    // These classes don't get spells at level 1
                    setMaxCantrips(0);
                    setMaxSpells(0);
                    break;
                default:
                    setMaxCantrips(0);
                    setMaxSpells(0);
                    break;
            }
        }

        // For racial spellcasting (High Elf), allow 1 cantrip if not already a spellcaster
        if (hasRacialSpellcasting() && !hasSpellcasting()) {
            setMaxCantrips(1);
            setShowExtraSpells(true);
        }
    }, [characterData.classId, hasSpellcasting, hasRacialSpellcasting]);

    // Fetch spells data
    useEffect(() => {
        if (!characterData.worldId) {
            setError("No world selected. Please go back to Step 1.");
            setIsLoading(false);
            return;
        }

        if (!hasSpellcasting() && !hasRacialSpellcasting()) {
            // If character can't cast spells, skip loading
            // But still update character data to indicate no spells
            updateCharacterData({
                spells: {
                    cantrips: [],
                    level1: [],
                    hasSpellcasting: false
                }
            });
            setIsLoading(false);
            return;
        }

        setIsLoading(true);
        setError(null);
        
        // Fetch data from the API using the world ID
        fetch(`/characters/api/creation-data/${characterData.worldId}`)
            .then(response => {
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                return response.json();
            })
            .then(data => {
                if (data.success && data.data) {
                    console.log("Spell data received:", data.data);
                    
                    // Filter spells by class
                    let classSpells = {
                        cantrips: [],
                        level1: []
                    };

                    // Add class-specific spells
                    if (data.data.spells && Array.isArray(data.data.spells)) {
                        // Properly filter by class
                        data.data.spells.forEach(spell => {
                            if (!spell.classes || !Array.isArray(spell.classes)) {
                                console.warn("Spell missing classes array:", spell.name);
                                return;
                            }
                            
                            // For regular spellcasting class
                            if (hasSpellcasting() && spell.classes.includes(characterData.classId)) {
                                if (spell.level === 0) {
                                    classSpells.cantrips.push(spell);
                                } else if (spell.level === 1) {
                                    classSpells.level1.push(spell);
                                }
                            }
                            // For racial spellcasting (High Elf), add wizard cantrips
                            else if (hasRacialSpellcasting() && !hasSpellcasting() && spell.level === 0) {
                                if (spell.classes.includes('wizard')) {
                                    classSpells.cantrips.push(spell);
                                }
                            }
                        });
                    }

                    // Sort spells by name
                    classSpells.cantrips.sort((a, b) => a.name.localeCompare(b.name));
                    classSpells.level1.sort((a, b) => a.name.localeCompare(b.name));

                    setAvailableSpells(classSpells);
                    setIsLoading(false);
                } else {
                    throw new Error(data.error || 'Invalid data format.');
                }
            })
            .catch(err => {
                console.error("Step7: Failed to fetch spells:", err);
                setError(`Failed to load spells: ${err.message}. Check your connection or try again later.`);
                setIsLoading(false);
            });
    }, [characterData.worldId, characterData.classId, hasSpellcasting, hasRacialSpellcasting, updateCharacterData]);

    // Handle spell selection
    const handleSpellSelect = (spellId, spellType) => {
        if (spellType === 'cantrip') {
            // Toggle selection
            if (selectedCantrips.includes(spellId)) {
                setSelectedCantrips(prev => prev.filter(id => id !== spellId));
            } else {
                // Check if at maximum
                if (selectedCantrips.length < maxCantrips) {
                    setSelectedCantrips(prev => [...prev, spellId]);
                } else {
                    alert(`You can only select ${maxCantrips} cantrips.`);
                }
            }
        } else {
            // Toggle selection for level 1 spells
            if (selectedSpells.includes(spellId)) {
                setSelectedSpells(prev => prev.filter(id => id !== spellId));
            } else {
                // Check if at maximum
                if (selectedSpells.length < maxSpells) {
                    setSelectedSpells(prev => [...prev, spellId]);
                } else {
                    alert(`You can only select ${maxSpells} 1st-level spells.`);
                }
            }
        }
    };

    // Handler for showing spell details
    const handleShowDetails = (spell) => {
        setShowSpellDetails(spell);
        
        // Add a slight delay before adding the active class for animation
        setTimeout(() => {
            if (spellDetailsRef.current) {
                spellDetailsRef.current.classList.add('active');
            }
        }, 10);
    };

    // Handler for closing spell details
    const handleCloseDetails = () => {
        if (spellDetailsRef.current) {
            spellDetailsRef.current.classList.remove('active');
            
            // Wait for animation to complete before removing modal
            setTimeout(() => {
                setShowSpellDetails(null);
            }, 400);
        } else {
            setShowSpellDetails(null);
        }
    };

    // Validate spell selections
    const validateSelections = () => {
        // Skip validation if character has no spellcasting
        if (!hasSpellcasting() && !hasRacialSpellcasting()) {
            return { valid: true };
        }

        // For spellcasting classes
        if (hasSpellcasting()) {
            // Check if the required number of cantrips is selected
            if (selectedCantrips.length < maxCantrips) {
                return {
                    valid: false,
                    message: `Please select ${maxCantrips} cantrips.`
                };
            }
            
            // Check if the required number of spells is selected (for classes that prepare spells)
            if (['wizard', 'cleric', 'druid'].includes(characterData.classId) && selectedSpells.length < maxSpells) {
                return {
                    valid: false,
                    message: `Please select ${maxSpells} 1st-level spells.`
                };
            }
        }
        
        // For racial spellcasting
        if (hasRacialSpellcasting() && !hasSpellcasting() && selectedCantrips.length < 1) {
            return {
                valid: false,
                message: "Please select your racial cantrip."
            };
        }
        
        return { valid: true };
    };

    // Handle continue button
    const handleContinue = () => {
        const validation = validateSelections();
        
        if (!validation.valid) {
            alert(validation.message);
            return;
        }
        
        // Get full spell objects for the selected spells
        const selectedCantripDetails = availableSpells.cantrips.filter(spell => 
            selectedCantrips.includes(spell.id)
        );
        
        const selectedSpellDetails = availableSpells.level1.filter(spell => 
            selectedSpells.includes(spell.id)
        );
        
        // Update character data with selected spells
        updateCharacterData({
            spells: {
                cantrips: selectedCantripDetails,
                level1: selectedSpellDetails,
                hasSpellcasting: hasSpellcasting() || hasRacialSpellcasting()
            }
        });
        
        // Move to next step
        nextStep();
    };

    // Skip step if character has no spellcasting
    const handleSkip = () => {
        // Update character data to indicate no spells
        updateCharacterData({
            spells: {
                cantrips: [],
                level1: [],
                hasSpellcasting: false
            }
        });
        
        // Move to next step
        nextStep();
    };

    // --- Render Logic ---
    if (isLoading) {
        return (
            <div className="loading-container">
                <div className="spinner-border" role="status"></div>
                <div>Loading Spell Options...</div>
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

    // If character has no spellcasting abilities, show options to skip
    if (!hasSpellcasting() && !hasRacialSpellcasting()) {
        return (
            <div className="step7-outer-container">
                <h2 className="step7-title">Spellcasting</h2>
                
                <div className="no-spells-container">
                    <div className="no-spells-message">
                        <i className="bi bi-magic"></i>
                        <h3>No Spellcasting Available</h3>
                        <p>Your character class ({characterData.className}) does not have spellcasting abilities at 1st level.</p>
                    </div>
                    
                    <button className="skip-button" onClick={handleSkip}>
                        Continue to Next Step <i className="bi bi-arrow-right"></i>
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="step7-outer-container">
            {/* Title */}
            <h2 className="step7-title">Spellcasting</h2>
            
            {/* Spell selection tabs */}
            <div className="spell-tabs">
                <div 
                    className={`spell-tab ${activeTab === 'cantrips' ? 'active' : ''}`}
                    onClick={() => setActiveTab('cantrips')}
                >
                    <i className="bi bi-stars"></i> Cantrips 
                    <span className="selection-counter">
                        {selectedCantrips.length}/{maxCantrips}
                    </span>
                </div>
                
                {hasSpellcasting() && maxSpells > 0 && (
                    <div 
                        className={`spell-tab ${activeTab === 'level1' ? 'active' : ''}`}
                        onClick={() => setActiveTab('level1')}
                    >
                        <i className="bi bi-book"></i> 1st-Level Spells
                        <span className="selection-counter">
                            {selectedSpells.length}/{maxSpells}
                        </span>
                    </div>
                )}
            </div>
            
            {/* Spellcasting explanation */}
            <div className="spellcasting-explanation">
                {activeTab === 'cantrips' && (
                    <div className="spellcasting-info">
                        <h3>Cantrips</h3>
                        <p>Cantrips are simple but powerful spells that can be cast at will, without using a spell slot or being prepared in advance.</p>
                        {hasRacialSpellcasting() && !hasSpellcasting() && (
                            <p className="racial-spellcasting-note">
                                As a High Elf, you know one cantrip of your choice from the wizard spell list.
                            </p>
                        )}
                        <p className="selection-instructions">
                            You must select {maxCantrips} cantrip{maxCantrips !== 1 ? 's' : ''}.
                        </p>
                    </div>
                )}
                
                {activeTab === 'level1' && (
                    <div className="spellcasting-info">
                        <h3>1st-Level Spells</h3>
                        <p>These spells require spell slots to cast. As a 1st-level {characterData.className}, you have two 1st-level spell slots.</p>
                        {['wizard', 'cleric', 'druid'].includes(characterData.classId) && (
                            <p className="preparation-note">
                                You prepare a number of spells equal to your {characterData.classId === 'wizard' ? 'Intelligence' : 'Wisdom'} modifier + your {characterData.className} level (minimum of one spell).
                            </p>
                        )}
                        {['sorcerer', 'bard', 'warlock'].includes(characterData.classId) && (
                            <p className="known-spells-note">
                                These are the spells you know. You don't need to prepare them.
                            </p>
                        )}
                        <p className="selection-instructions">
                            You must select {maxSpells} 1st-level spell{maxSpells !== 1 ? 's' : ''}.
                        </p>
                    </div>
                )}
            </div>
            
            {/* Spell list */}
            <div className="spell-selection-container">
                {activeTab === 'cantrips' && (
                    <div className="spell-list">
                        {availableSpells.cantrips.map(spell => (
                            <div 
                                key={spell.id} 
                                className={`spell-card ${selectedCantrips.includes(spell.id) ? 'selected' : ''}`}
                                onClick={() => handleSpellSelect(spell.id, 'cantrip')}
                            >
                                <div className="spell-header">
                                    <h3 className="spell-name">{spell.name}</h3>
                                    <div className="spell-school">{spell.school}</div>
                                </div>
                                
                                <div className="spell-casting-time">
                                    <i className="bi bi-clock"></i> {spell.casting_time}
                                </div>
                                
                                <div className="spell-range">
                                    <i className="bi bi-arrows-angle-expand"></i> {spell.range}
                                </div>
                                
                                <p className="spell-description">
                                    {spell.shortDescription}
                                </p>
                                
                                <button 
                                    className="details-button"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        handleShowDetails(spell);
                                    }}
                                >
                                    See Details
                                </button>
                                
                                <div className="selected-indicator">
                                    <i className="bi bi-check-circle-fill"></i> Selected
                                </div>
                            </div>
                        ))}
                    </div>
                )}
                
                {activeTab === 'level1' && (
                    <div className="spell-list">
                        {availableSpells.level1.map(spell => (
                            <div 
                                key={spell.id} 
                                className={`spell-card ${selectedSpells.includes(spell.id) ? 'selected' : ''}`}
                                onClick={() => handleSpellSelect(spell.id, 'level1')}
                            >
                                <div className="spell-header">
                                    <h3 className="spell-name">{spell.name}</h3>
                                    <div className="spell-school">{spell.school}</div>
                                </div>
                                
                                <div className="spell-casting-time">
                                    <i className="bi bi-clock"></i> {spell.casting_time}
                                </div>
                                
                                <div className="spell-range">
                                    <i className="bi bi-arrows-angle-expand"></i> {spell.range}
                                </div>
                                
                                <p className="spell-description">
                                    {spell.shortDescription}
                                </p>
                                
                                <button 
                                    className="details-button"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        handleShowDetails(spell);
                                    }}
                                >
                                    See Details
                                </button>
                                
                                <div className="selected-indicator">
                                    <i className="bi bi-check-circle-fill"></i> Selected
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
            
            {/* Spell details modal */}
            {showSpellDetails && (
                <div 
                    className="spell-details-overlay" 
                    ref={spellDetailsRef} 
                    onClick={handleCloseDetails}
                >
                    <div className="spell-details-modal" onClick={(e) => e.stopPropagation()}>
                        <button className="close-button" onClick={handleCloseDetails}>×</button>
                        
                        <div className="spell-details-header">
                            <h3 className="spell-details-name">{showSpellDetails.name}</h3>
                            <div className="spell-details-level-school">
                                {showSpellDetails.level === 0 ? 'Cantrip' : `${showSpellDetails.level}st-level`} {showSpellDetails.school}
                            </div>
                        </div>
                        
                        <div className="spell-details-content">
                            <div className="spell-details-properties">
                                <div className="spell-property">
                                    <span className="property-label">Casting Time:</span>
                                    <span className="property-value">{showSpellDetails.casting_time}</span>
                                </div>
                                
                                <div className="spell-property">
                                    <span className="property-label">Range:</span>
                                    <span className="property-value">{showSpellDetails.range}</span>
                                </div>
                                
                                <div className="spell-property">
                                    <span className="property-label">Components:</span>
                                    <span className="property-value">{showSpellDetails.components}</span>
                                </div>
                                
                                <div className="spell-property">
                                    <span className="property-label">Duration:</span>
                                    <span className="property-value">{showSpellDetails.duration}</span>
                                </div>
                            </div>
                            
                            <div className="spell-details-description">
                                <p>{showSpellDetails.description}</p>
                                
                                {showSpellDetails.atHigherLevels && (
                                    <div className="at-higher-levels">
                                        <h4>At Higher Levels</h4>
                                        <p>{showSpellDetails.atHigherLevels}</p>
                                    </div>
                                )}
                            </div>
                            
                            {showSpellDetails.damage && (
                                <div className="spell-damage-info">
                                    <h4>Damage</h4>
                                    <p>{showSpellDetails.damage.diceCount}{showSpellDetails.damage.diceType} {showSpellDetails.damage.type}</p>
                                </div>
                            )}
                            
                            <div className="spell-classes">
                                <h4>Classes</h4>
                                <p>{showSpellDetails.classes.join(', ')}</p>
                            </div>
                        </div>
                    </div>
                </div>
            )}
            
            {/* Validation message */}
            <div className="validation-container">
                {activeTab === 'cantrips' && selectedCantrips.length !== maxCantrips && (
                    <div className="validation-message">
                        Please select {maxCantrips - selectedCantrips.length} more cantrip{maxCantrips - selectedCantrips.length !== 1 ? 's' : ''}.
                    </div>
                )}
                
                {activeTab === 'level1' && ['wizard', 'cleric', 'druid'].includes(characterData.classId) && selectedSpells.length !== maxSpells && (
                    <div className="validation-message">
                        Please select {maxSpells - selectedSpells.length} more spell{maxSpells - selectedSpells.length !== 1 ? 's' : ''}.
                    </div>
                )}
            </div>
            
            {/* Navigation Buttons */}
            <div className="step7-navigation">
                <button className="back-button" onClick={prevStep}>
                    <i className="bi bi-arrow-left"></i> Back to Class Features
                </button>
                
                <button 
                    className={`continue-button ${validateSelections().valid ? 'active' : ''}`}
                    onClick={handleContinue}
                    disabled={!validateSelections().valid}
                >
                    Continue to Skills <i className="bi bi-arrow-right"></i>
                </button>
            </div>
        </div>
    );
}

export default Step7_SpellSelector;