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

    const classMatchesSpell = useCallback((classId, spellClasses) => {
        if (!spellClasses || !classId) {
            return false;
        }
    
        const normalizedClassId = classId.toLowerCase().trim(); // Ensure lowercase and no extra spaces
    
        if (typeof spellClasses === 'string') {
            const classesArray = spellClasses.toLowerCase().split(/,\s*/).map(c => c.trim());
            const match = classesArray.includes(normalizedClassId);
            return match;
        }
    
        // 2. Handle if spellClasses is an array
        if (Array.isArray(spellClasses)) {
            const match = spellClasses.some(c =>
                typeof c === 'string' && c.toLowerCase().trim() === normalizedClassId
            );
            return match;
        }
    
        console.warn(`Unexpected spellClasses format for class '${normalizedClassId}':`, spellClasses, `(Type: ${typeof spellClasses})`);
        return false; // Default to false if format is unrecognized
    
    }, []);

    // Determine if the class can cast spells
    const hasSpellcasting = useCallback(() => {
        if (characterData.classData && characterData.classData.spellcasting) {
            return true;
        }
        
        // Fallback to list of known spellcasting classes
        const spellcastingClasses = ['wizard', 'sorcerer', 'bard', 'cleric', 'druid', 'paladin', 'ranger', 'warlock'];
        return spellcastingClasses.includes(characterData.classId.toLowerCase());
    }, [characterData.classId, characterData.classData]);

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

    // Get spell slots based on class data
    useEffect(() => {
        if (!hasSpellcasting() && !hasRacialSpellcasting()) {
            setIsLoading(false);
            return;
        }
        
        console.log("Character data for spellcasting:", characterData);
        
        // Extract spell counts from the spellcasting progression
        if (characterData.classData && characterData.classData.spellcasting) {
            const spellcasting = characterData.classData.spellcasting;
            const level1Data = spellcasting.progression?.level1;
            
            if (level1Data) {
                // Set cantrips count
                console.log("Level 1 spell data found:", level1Data);
                setMaxCantrips(level1Data.cantrips_known || 0);
                
                // Set spells count based on spellcasting type
                if (spellcasting.spellcasting_type === 'known') {
                    // Known spellcasters like bards and sorcerers have a fixed number
                    setMaxSpells(level1Data.spells_known || 0);
                    console.log(`Known spellcaster: ${maxSpells} spells`);
                } 
                else if (spellcasting.spellcasting_type === 'prepared') {
                    // Prepared spellcasters like clerics and druids use an ability modifier formula
                    const abilityName = spellcasting.ability.toLowerCase();
                    const abilityScore = characterData.finalAbilityScores?.[abilityName] || 10;
                    const abilityModifier = Math.floor((abilityScore - 10) / 2);
                    
                    // At level 1, they can prepare ability modifier + level (minimum 1)
                    const preparedCount = Math.max(1, abilityModifier + 1);
                    setMaxSpells(preparedCount);
                    console.log(`Prepared spellcaster: ${abilityName} mod (${abilityModifier}) + 1 = ${preparedCount} spells`);
                }
            } else {
                console.log("No level 1 data found in spellcasting progression");
            }
        } else {
            console.log("No spellcasting data found in class data");
        }
        
        // For racial spellcasting
        if (hasRacialSpellcasting() && !hasSpellcasting()) {
            setMaxCantrips(1);
            setShowExtraSpells(true);
            console.log("Racial spellcasting detected: 1 cantrip available");
        }
    }, [characterData.classData, characterData.finalAbilityScores, hasSpellcasting, hasRacialSpellcasting]);

    // Fetch spells data

    useEffect(() => {
        if (!characterData.worldId) {
            setError("No world selected. Please go back to Step 1.");
            setIsLoading(false);
            return;
        }
    
        if (!hasSpellcasting() && !hasRacialSpellcasting()) {
            // If character can't cast spells, skip loading
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
                    
                    // Debug - log a sample spell to understand structure
                    if (data.data.spells && data.data.spells.length > 0) {
                        console.log("Sample spell structure:", JSON.stringify(data.data.spells[0], null, 2));
                    }
                    
                    // Filter spells by class
                    let classSpells = {
                        cantrips: [],
                        level1: []
                    };
    
                    // Debug output for spell filtering
                    console.log(`Filtering spells for class: ${characterData.classId}`);
                    
                    // Add class-specific spells
                    if (data.data.spells && Array.isArray(data.data.spells)) {
                        // Count how many spells are available before filtering
                        const cantripsBeforeFilter = data.data.spells.filter(s => s.level === 0).length;
                        const level1BeforeFilter = data.data.spells.filter(s => s.level === 1).length;
                        console.log(`Available before filtering: ${cantripsBeforeFilter} cantrips, ${level1BeforeFilter} level 1 spells`);
                        
                        console.log("Step7: Raw spell data received:", JSON.stringify(data.data.spells, null, 2));
                        console.log("Step7: Current classId for filtering:", characterData.classId);
                        console.log("Step7: hasSpellcasting() check:", hasSpellcasting()); // Check this too

                        let filteredCantrips = [];
                        let filteredLevel1Spells = [];

                        // Properly filter by class
                        data.data.spells.forEach(spell => {
                            if (!spell || !spell.name) {
                                console.warn("Skipping invalid spell data:", spell);
                                return; // Skip this iteration if spell data is malformed
                            }
                        
                            const spellClasses = spell.classes; // Get the classes field
                            const currentClassId = characterData.classId;
                        
                            // **Log the types and values being compared**
                            console.log(`--- Filtering Spell: ${spell.name} (Level ${spell.level}) ---`);
                            console.log(`   Current Class ID: '${currentClassId}' (Type: ${typeof currentClassId})`);
                            // **Crucially log the spell.classes value and type**
                            console.log(`   Spell Available Classes Field:`, spellClasses, `(Type: ${typeof spellClasses}, IsArray: ${Array.isArray(spellClasses)})`);
                        
                            // Perform the check
                            const isMatch = classMatchesSpell(currentClassId, spellClasses);
                            console.log(`   Match Result for '${currentClassId}': ${isMatch}`);
                        
                            // Add to temporary arrays if match is found
                            if (hasSpellcasting() && isMatch) {
                              if (spell.level === 0) {
                                filteredCantrips.push(spell);
                                console.log(`   >>> Matched Cantrip: ${spell.name}`);
                              } else if (spell.level === 1) {
                                filteredLevel1Spells.push(spell);
                                console.log(`   >>> Matched Level 1 Spell: ${spell.name}`);
                              }
                            } else if (hasRacialSpellcasting() && !hasSpellcasting() && spell.level === 0) {
                              // Handle racial spellcasting separately if needed
                              if (classMatchesSpell('wizard', spellClasses)) { // Example: High Elf
                                  // Add logic for racial spells
                              }
                            }
                        });
                        
                        // Log the results after filtering
                        console.log(`After filtering: ${classSpells.cantrips.length} cantrips, ${classSpells.level1.length} level 1 spells`);
                    }
    
                    // Sort spells by name
                    filteredCantrips.sort((a, b) => a.name.localeCompare(b.name));
                    filteredLevel1Spells.sort((a, b) => a.name.localeCompare(b.name));
    
                    setAvailableSpells({
                        cantrips: filteredCantrips,
                        level1: filteredLevel1Spells
                    });
                    
                    console.log(`After filtering: ${filteredCantrips.length} cantrips, ${filteredLevel1Spells.length} level 1 spells`);

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