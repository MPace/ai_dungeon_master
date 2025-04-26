// File: frontend/src/components/steps/Step11_CharacterReview.jsx - Equipment rendering fix

import React, { useState, useEffect } from 'react';
import './Step11_CharacterReview.css';

function Step11_CharacterReview({ characterData, updateCharacterData, nextStep, prevStep }) {
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [isSaving, setIsSaving] = useState(false);
    const [savingSuccess, setSavingSuccess] = useState(false);
    const [savingError, setSavingError] = useState(null);
    const [calculatedStats, setCalculatedStats] = useState({
        hitPoints: 0,
        armorClass: 10,
        initiative: 0,
        proficiencyBonus: 2, // At level 1
        speed: 30 // Default
    });

    // Calculate derived statistics like Hit Points and Armor Class
    useEffect(() => {
        if (!characterData) return;

        try {
            // Calculate Hit Points based on class
            let hitPoints = 0;
            const constitutionModifier = Math.floor((characterData.finalAbilityScores?.constitution - 10) / 2) || 0;

            // Different classes have different hit dice
            switch (characterData.classId) {
                case 'barbarian':
                    hitPoints = 12 + constitutionModifier;
                    break;
                case 'fighter':
                case 'paladin':
                case 'ranger':
                    hitPoints = 10 + constitutionModifier;
                    break;
                case 'bard':
                case 'cleric':
                case 'druid':
                case 'monk':
                case 'rogue':
                case 'warlock':
                    hitPoints = 8 + constitutionModifier;
                    break;
                case 'sorcerer':
                case 'wizard':
                    hitPoints = 6 + constitutionModifier;
                    break;
                default:
                    hitPoints = 8 + constitutionModifier; // Default
            }

            // Get character speed from race data
            let speed = 30; // Default speed
            if (characterData.raceData && characterData.raceData.traits) {
                const speedTrait = characterData.raceData.traits.find(trait => 
                    trait.name.toLowerCase().includes('speed'));
                
                if (speedTrait) {
                    // Extract the number from the trait description using regex
                    const speedMatch = speedTrait.description.match(/(\d+)\s*feet/);
                    if (speedMatch && speedMatch[1]) {
                        speed = parseInt(speedMatch[1]);
                    }
                }
            }

            // Calculate base Armor Class
            let armorClass = 10 + Math.floor((characterData.finalAbilityScores?.dexterity - 10) / 2);

            // Check equipped armor
            if (characterData.equipment && characterData.equipment.equipped) {
                // Check if character has armor equipped
                const armor = characterData.equipment.equipped.find(item => 
                    item.type && item.type.toLowerCase().includes('armor'));
                
                // Check if character has a shield
                const shield = characterData.equipment.equipped.find(item => 
                    item.item && item.item.toLowerCase().includes('shield'));
                
                // Apply armor bonus if found
                if (armor) {
                    // This is simplified - would need to check armor type and handle specific rules
                    armorClass = 12 + Math.min(2, Math.floor((characterData.finalAbilityScores?.dexterity - 10) / 2));
                }
                
                // Apply shield bonus if found
                if (shield) {
                    armorClass += 2; // Standard shield bonus
                }
            }

            // Calculate Initiative (DEX modifier)
            const initiative = Math.floor((characterData.finalAbilityScores?.dexterity - 10) / 2);

            setCalculatedStats({
                hitPoints,
                armorClass,
                initiative,
                proficiencyBonus: 2,
                speed
            });
        } catch (err) {
            console.error("Error calculating character statistics:", err);
            setError("Could not calculate character statistics. Please check your selections.");
        }
    }, [characterData]);

    // Transform character data for backend
    const transformCharacterForBackend = (reactCharacterData) => {
        return {
            name: reactCharacterData.characterName || '',
            race: reactCharacterData.raceName || '',
            class: reactCharacterData.className || '',
            character_class: reactCharacterData.className || '', // Include both for compatibility
            background: reactCharacterData.backgroundName || '',
            level: reactCharacterData.level || 1,
            abilities: reactCharacterData.finalAbilityScores || {},
            skills: reactCharacterData.proficiencies?.skills || [],
            equipment: reactCharacterData.equipment || {},
            features: reactCharacterData.classFeatures || {},
            spellcasting: reactCharacterData.spells || {},
            hitPoints: {
                current: reactCharacterData.calculatedStats?.hitPoints || 10,
                max: reactCharacterData.calculatedStats?.hitPoints || 10,
                hitDie: reactCharacterData.className?.toLowerCase() === 'barbarian' ? 'd12' : 
                        ['fighter', 'paladin', 'ranger'].includes(reactCharacterData.className?.toLowerCase()) ? 'd10' :
                        ['sorcerer', 'wizard'].includes(reactCharacterData.className?.toLowerCase()) ? 'd6' : 'd8'
            },
            description: reactCharacterData.description || '',
            // Keep metadata fields
            character_id: reactCharacterData.character_id,
            isDraft: reactCharacterData.isDraft || false,
            submissionId: reactCharacterData.submissionId
        };
    };

    // Get ability modifier with sign
    const getModifier = (abilityScore) => {
        if (!abilityScore) return "+0";
        const modifier = Math.floor((abilityScore - 10) / 2);
        return modifier >= 0 ? `+${modifier}` : `${modifier}`;
    };

    // Safely render an equipment item - handles various item formats
    const renderEquipmentItem = (item, index) => {
        // Early return for null/undefined
        if (!item) {
            console.warn("Encountered null or undefined equipment item");
            return null;
        }

        // Determine the item name to display
        let itemName = "";
        let itemType = null;

        if (typeof item === 'string') {
            // If item is a plain string
            itemName = item;
        } else if (typeof item === 'object') {
            // If item is an object, try to extract properties safely
            if (item.item) {
                itemName = item.item;
            } else if (item.name) {
                itemName = item.name;
            } else if (item.id) {
                itemName = item.id;
            } else {
                itemName = "Unknown Item";
                console.warn("Equipment item missing name/item/id:", item);
            }

            // Get type if available
            itemType = item.type;
        } else {
            // Fallback for unexpected types
            itemName = "Unrecognized Item";
            console.warn("Equipment item of unexpected type:", typeof item, item);
        }

        // Now render with the extracted name and type
        return (
            <div key={index} className="review-equipment-item">
                <div className="review-item-name">{itemName}</div>
                {itemType && <div className="review-item-type">{itemType}</div>}
            </div>
        );
    };

    // Handle finalize and save character
    const handleSaveCharacter = async (andPlay = false) => {
        if (isSaving) return;
        
        setIsSaving(true);
        setSavingError(null);
        
        try {
            // Prepare character data with our transform function
            const submissionId = Math.random().toString(36).substring(2) + Date.now().toString(36);
            
            // First, create a complete character object with all React data
            const completeReactData = {
                ...characterData,
                isDraft: false,
                completedAt: new Date().toISOString(),
                submissionId,
                calculatedStats
            };
            
            // Then transform it to the format the backend expects
            const backendCharacterData = transformCharacterForBackend(completeReactData);
            
            // Send to API
            const response = await fetch('/characters/api/save-character', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    // Get CSRF token from meta tag
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
                },
                body: JSON.stringify(backendCharacterData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                console.log("Character saved successfully:", data);
                setSavingSuccess(true);
                
                // If player wants to play immediately
                if (andPlay) {
                    // Redirect to game page
                    window.location.href = `/game/play/${data.character_id}`;
                } else {
                    // Redirect to dashboard
                    window.location.href = '/game/dashboard';
                }
            } else {
                setSavingError(data.error || "Failed to save character. Please try again.");
            }
        } catch (err) {
            console.error("Error saving character:", err);
            setSavingError("Network error. Please check your connection and try again.");
        } finally {
            setIsSaving(false);
        }
    };

    return (
        <div className="step11-outer-container">
            {/* Title */}
            <h2 className="step11-title">Review Your Character</h2>
            
            {error && (
                <div className="review-error-alert">
                    {error}
                </div>
            )}
            
            {savingError && (
                <div className="review-error-alert">
                    {savingError}
                </div>
            )}
            
            {/* Character Summary Header */}
            <div className="review-character-header">
                <div className="review-character-name-container">
                    <h3 className="review-character-name">{characterData.characterName || "Unnamed Character"}</h3>
                    <div className="review-character-subtitle">
                        {characterData.raceName} {characterData.subraceName && `(${characterData.subraceName})`} {characterData.className}
                    </div>
                    <div className="review-character-background">
                        {characterData.backgroundName} Background
                    </div>
                </div>
                
                <div className="review-vital-stats-container">
                    <div className="review-vital-stat">
                        <div className="review-stat-value">{calculatedStats.hitPoints}</div>
                        <div className="review-stat-label">Hit Points</div>
                    </div>
                    
                    <div className="review-vital-stat">
                        <div className="review-stat-value">{calculatedStats.armorClass}</div>
                        <div className="review-stat-label">Armor Class</div>
                    </div>
                    
                    <div className="review-vital-stat">
                        <div className="review-stat-value">{getModifier(characterData.finalAbilityScores?.dexterity)}</div>
                        <div className="review-stat-label">Initiative</div>
                    </div>
                    
                    <div className="review-vital-stat">
                        <div className="review-stat-value">+{calculatedStats.proficiencyBonus}</div>
                        <div className="review-stat-label">Proficiency</div>
                    </div>
                    
                    <div className="review-vital-stat">
                        <div className="review-stat-value">{calculatedStats.speed}</div>
                        <div className="review-stat-label">Speed</div>
                    </div>
                </div>
            </div>
            
            {/* Main content sections */}
            <div className="review-character-details-grid">
                {/* Left Column */}
                <div className="review-details-column">
                    {/* Ability Scores */}
                    <div className="review-details-section">
                        <h3 className="review-section-title">Ability Scores</h3>
                        <div className="review-ability-scores-container">
                            {characterData.finalAbilityScores && Object.entries(characterData.finalAbilityScores).map(([ability, score]) => (
                                <div key={ability} className="review-ability-score-box">
                                    <div className="review-ability-name">{ability.substring(0, 3).toUpperCase()}</div>
                                    <div className="review-ability-value">{score}</div>
                                    <div className="review-ability-modifier">{getModifier(score)}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                    
                    {/* Proficiencies */}
                    <div className="review-details-section">
                        <h3 className="review-section-title">Proficiencies</h3>
                        <div className="review-proficiencies-list">
                            {characterData.proficiencies?.skills?.map((skill, index) => (
                                <div key={index} className="review-proficiency-item">
                                    <i className="bi bi-check-circle-fill"></i> {skill}
                                </div>
                            ))}
                            {(!characterData.proficiencies?.skills || characterData.proficiencies.skills.length === 0) && (
                                <div className="review-empty-message">No proficiencies selected</div>
                            )}
                        </div>
                    </div>
                    
                    {/* Class Features */}
                    <div className="review-details-section">
                        <h3 className="review-section-title">Class Features</h3>
                        <div className="review-features-list">
                            {/* Standard Features */}
                            {characterData.classFeatures?.standard?.map((feature, index) => (
                                <div key={index} className="review-feature-item">
                                    <div className="review-feature-name">{feature}</div>
                                </div>
                            ))}
                            
                            {/* Choices */}
                            {characterData.classFeatures?.choices && Object.entries(characterData.classFeatures.choices).map(([featureName, choiceId], index) => (
                                <div key={index} className="review-feature-item choice">
                                    <div className="review-feature-name">{featureName}: {choiceId}</div>
                                </div>
                            ))}
                            
                            {(!characterData.classFeatures?.standard && !characterData.classFeatures?.choices) && (
                                <div className="review-empty-message">No class features</div>
                            )}
                        </div>
                    </div>
                    
                    {/* Equipment - with improved rendering */}
                    <div className="review-details-section">
                        <h3 className="review-section-title">Equipment</h3>
                        <div className="review-equipment-list">
                            {characterData.equipment?.equipped?.map((item, index) => renderEquipmentItem(item, index))}
                            {(!characterData.equipment?.equipped || characterData.equipment.equipped.length === 0) && (
                                <div className="review-empty-message">No equipment selected</div>
                            )}
                        </div>
                    </div>
                </div>
                
                {/* Right Column */}
                <div className="review-details-column">
                    {/* Character Info */}
                    <div className="review-details-section">
                        <h3 className="review-section-title">Character Information</h3>
                        <div className="review-character-info-container">
                            <div className="review-info-row">
                                <div className="review-info-label">World:</div>
                                <div className="review-info-value">{characterData.worldName}</div>
                            </div>
                            
                            <div className="review-info-row">
                                <div className="review-info-label">Campaign:</div>
                                <div className="review-info-value">{characterData.campaignName}</div>
                            </div>
                            
                            <div className="review-info-row">
                                <div className="review-info-label">Race:</div>
                                <div className="review-info-value">
                                    {characterData.raceName} {characterData.subraceName && `(${characterData.subraceName})`}
                                </div>
                            </div>
                            
                            <div className="review-info-row">
                                <div className="review-info-label">Class:</div>
                                <div className="review-info-value">{characterData.className}</div>
                            </div>
                            
                            <div className="review-info-row">
                                <div className="review-info-label">Background:</div>
                                <div className="review-info-value">{characterData.backgroundName}</div>
                            </div>
                            
                            <div className="review-info-row">
                                <div className="review-info-label">Gender:</div>
                                <div className="review-info-value">{characterData.gender}</div>
                            </div>
                            
                            <div className="review-info-row">
                                <div className="review-info-label">Level:</div>
                                <div className="review-info-value">1</div>
                            </div>
                        </div>
                    </div>
                    
                    {/* Spells Section - only shown for spellcasters */}
                    {characterData.spells && characterData.spells.hasSpellcasting && (
                        <div className="review-details-section">
                            <h3 className="review-section-title">Spells</h3>
                            
                            {/* Cantrips */}
                            {characterData.spells.cantrips && characterData.spells.cantrips.length > 0 && (
                                <div className="review-spell-group">
                                    <h4 className="review-spell-level-title">Cantrips</h4>
                                    <div className="review-spell-list">
                                        {characterData.spells.cantrips.map((spell, index) => (
                                            <div key={index} className="review-spell-item">
                                                <div className="review-spell-name">{spell.name}</div>
                                                <div className="review-spell-school">{spell.school}</div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                            
                            {/* 1st Level Spells */}
                            {characterData.spells.level1 && characterData.spells.level1.length > 0 && (
                                <div className="review-spell-group">
                                    <h4 className="review-spell-level-title">1st Level Spells</h4>
                                    <div className="review-spell-list">
                                        {characterData.spells.level1.map((spell, index) => (
                                            <div key={index} className="review-spell-item">
                                                <div className="review-spell-name">{spell.name}</div>
                                                <div className="review-spell-school">{spell.school}</div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                            
                            {(!characterData.spells.cantrips || characterData.spells.cantrips.length === 0) && 
                             (!characterData.spells.level1 || characterData.spells.level1.length === 0) && (
                                <div className="review-empty-message">No spells selected</div>
                            )}
                        </div>
                    )}
                    
                    {/* Racial Traits */}
                    <div className="review-details-section">
                        <h3 className="review-section-title">Racial Traits</h3>
                        <div className="review-traits-list">
                            {characterData.raceData?.traits?.map((trait, index) => (
                                <div key={index} className="review-trait-item">
                                    <div className="review-feature-name">{trait.name}</div>
                                    <div className="review-trait-description">{trait.description}</div>
                                </div>
                            ))}
                            
                            {/* Subrace traits if available */}
                            {characterData.raceData?.subraces?.map(subrace => {
                                if (subrace.id === characterData.subraceId && subrace.traits) {
                                    return subrace.traits.map((trait, index) => (
                                        <div key={`subrace-${index}`} className="review-trait-item subrace">
                                            <div className="review-feature-name">{trait.name}</div>
                                            <div className="review-trait-description">{trait.description}</div>
                                        </div>
                                    ));
                                }
                                return null;
                            })}
                            
                            {(!characterData.raceData?.traits || characterData.raceData.traits.length === 0) && (
                                <div className="review-empty-message">No racial traits</div>
                            )}
                        </div>
                    </div>
                    
                    {/* Background Features */}
                    <div className="review-details-section">
                        <h3 className="review-section-title">Background Feature</h3>
                        <div className="review-background-feature">
                            {characterData.backgroundFeature ? (
                                <>
                                    <div className="review-feature-name">{characterData.backgroundFeature.name}</div>
                                    <div className="review-feature-description">{characterData.backgroundFeature.description}</div>
                                </>
                            ) : (
                                <div className="review-empty-message">No background feature</div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
            
            {/* Action Buttons */}
            <div className="step11-navigation">
                <button className="review-back-button" onClick={prevStep}>
                    <i className="bi bi-arrow-left"></i> Back to Alignment
                </button>
                
                <div className="review-finalize-buttons">
                    <button 
                        className="review-save-play-button" 
                        onClick={() => handleSaveCharacter(true)}
                        disabled={isSaving}
                    >
                        {isSaving ? (
                            <><span className="spinner-border spinner-border-sm"></span> Saving...</>
                        ) : (
                            <><i className="bi bi-play-fill"></i> Save & Play</>
                        )}
                    </button>
                    
                    <button 
                        className="review-save-button" 
                        onClick={() => handleSaveCharacter(false)}
                        disabled={isSaving}
                    >
                        {isSaving ? (
                            <><span className="spinner-border spinner-border-sm"></span> Saving...</>
                        ) : (
                            <><i className="bi bi-save"></i> Save & Return to Dashboard</>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
}

export default Step11_CharacterReview;