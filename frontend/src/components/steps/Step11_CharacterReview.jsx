// File: frontend/src/components/steps/Step10_ReviewFinalize.jsx

import React, { useState, useEffect } from 'react';
import './Step10_ReviewFinalize.css';

function Step10_ReviewFinalize({ characterData, updateCharacterData, nextStep, prevStep }) {
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

    // Get ability modifier with sign
    const getModifier = (abilityScore) => {
        if (!abilityScore) return "+0";
        const modifier = Math.floor((abilityScore - 10) / 2);
        return modifier >= 0 ? `+${modifier}` : `${modifier}`;
    };

    // Handle finalize and save character
    const handleSaveCharacter = async (andPlay = false) => {
        if (isSaving) return;
        
        setIsSaving(true);
        setSavingError(null);
        
        try {
            // Prepare character data
            const finalCharacterData = {
                ...characterData,
                isDraft: false,
                completedAt: new Date().toISOString(),
                submissionId: Math.random().toString(36).substring(2) + Date.now().toString(36), // Generate unique ID
                calculatedStats
            };
            
            // Send to API
            const response = await fetch('/characters/api/save-character', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    // Get CSRF token from meta tag
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
                },
                body: JSON.stringify(finalCharacterData)
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
        <div className="step10-outer-container">
            {/* Title */}
            <h2 className="step10-title">Review Your Character</h2>
            
            {error && (
                <div className="error-alert">
                    {error}
                </div>
            )}
            
            {savingError && (
                <div className="error-alert">
                    {savingError}
                </div>
            )}
            
            {/* Character Summary Header */}
            <div className="character-header">
                <div className="character-name-container">
                    <h3 className="character-name">{characterData.characterName || "Unnamed Character"}</h3>
                    <div className="character-subtitle">
                        {characterData.raceName} {characterData.subraceName && `(${characterData.subraceName})`} {characterData.className}
                    </div>
                    <div className="character-background">
                        {characterData.backgroundName} Background
                    </div>
                </div>
                
                <div className="vital-stats-container">
                    <div className="vital-stat">
                        <div className="stat-value">{calculatedStats.hitPoints}</div>
                        <div className="stat-label">Hit Points</div>
                    </div>
                    
                    <div className="vital-stat">
                        <div className="stat-value">{calculatedStats.armorClass}</div>
                        <div className="stat-label">Armor Class</div>
                    </div>
                    
                    <div className="vital-stat">
                        <div className="stat-value">{getModifier(characterData.finalAbilityScores?.dexterity)}</div>
                        <div className="stat-label">Initiative</div>
                    </div>
                    
                    <div className="vital-stat">
                        <div className="stat-value">+{calculatedStats.proficiencyBonus}</div>
                        <div className="stat-label">Proficiency</div>
                    </div>
                    
                    <div className="vital-stat">
                        <div className="stat-value">{calculatedStats.speed}</div>
                        <div className="stat-label">Speed</div>
                    </div>
                </div>
            </div>
            
            {/* Main content sections */}
            <div className="character-details-grid">
                {/* Left Column */}
                <div className="details-column">
                    {/* Ability Scores */}
                    <div className="details-section">
                        <h3 className="section-title">Ability Scores</h3>
                        <div className="ability-scores-container">
                            {characterData.finalAbilityScores && Object.entries(characterData.finalAbilityScores).map(([ability, score]) => (
                                <div key={ability} className="ability-score-box">
                                    <div className="ability-name">{ability.substring(0, 3).toUpperCase()}</div>
                                    <div className="ability-value">{score}</div>
                                    <div className="ability-modifier">{getModifier(score)}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                    
                    {/* Proficiencies */}
                    <div className="details-section">
                        <h3 className="section-title">Proficiencies</h3>
                        <div className="proficiencies-list">
                            {characterData.proficiencies?.skills?.map((skill, index) => (
                                <div key={index} className="proficiency-item">
                                    <i className="bi bi-check-circle-fill"></i> {skill}
                                </div>
                            ))}
                            {(!characterData.proficiencies?.skills || characterData.proficiencies.skills.length === 0) && (
                                <div className="empty-message">No proficiencies selected</div>
                            )}
                        </div>
                    </div>
                    
                    {/* Class Features */}
                    <div className="details-section">
                        <h3 className="section-title">Class Features</h3>
                        <div className="features-list">
                            {/* Standard Features */}
                            {characterData.classFeatures?.standard?.map((feature, index) => (
                                <div key={index} className="feature-item">
                                    <div className="feature-name">{feature}</div>
                                </div>
                            ))}
                            
                            {/* Choices */}
                            {characterData.classFeatures?.choices && Object.entries(characterData.classFeatures.choices).map(([featureName, choiceId], index) => (
                                <div key={index} className="feature-item choice">
                                    <div className="feature-name">{featureName}: {choiceId}</div>
                                </div>
                            ))}
                            
                            {(!characterData.classFeatures?.standard && !characterData.classFeatures?.choices) && (
                                <div className="empty-message">No class features</div>
                            )}
                        </div>
                    </div>
                    
                    {/* Equipment */}
                    <div className="details-section">
                        <h3 className="section-title">Equipment</h3>
                        <div className="equipment-list">
                            {characterData.equipment?.equipped?.map((item, index) => (
                                <div key={index} className="equipment-item">
                                    <div className="item-name">
                                        {typeof item === 'string' ? item : item.item}
                                    </div>
                                    {item.type && <div className="item-type">{item.type}</div>}
                                </div>
                            ))}
                            {(!characterData.equipment?.equipped || characterData.equipment.equipped.length === 0) && (
                                <div className="empty-message">No equipment selected</div>
                            )}
                        </div>
                    </div>
                </div>
                
                {/* Right Column */}
                <div className="details-column">
                    {/* Character Info */}
                    <div className="details-section">
                        <h3 className="section-title">Character Information</h3>
                        <div className="character-info-container">
                            <div className="info-row">
                                <div className="info-label">World:</div>
                                <div className="info-value">{characterData.worldName}</div>
                            </div>
                            
                            <div className="info-row">
                                <div className="info-label">Campaign:</div>
                                <div className="info-value">{characterData.campaignName}</div>
                            </div>
                            
                            <div className="info-row">
                                <div className="info-label">Race:</div>
                                <div className="info-value">
                                    {characterData.raceName} {characterData.subraceName && `(${characterData.subraceName})`}
                                </div>
                            </div>
                            
                            <div className="info-row">
                                <div className="info-label">Class:</div>
                                <div className="info-value">{characterData.className}</div>
                            </div>
                            
                            <div className="info-row">
                                <div className="info-label">Background:</div>
                                <div className="info-value">{characterData.backgroundName}</div>
                            </div>
                            
                            <div className="info-row">
                                <div className="info-label">Gender:</div>
                                <div className="info-value">{characterData.gender}</div>
                            </div>
                            
                            <div className="info-row">
                                <div className="info-label">Level:</div>
                                <div className="info-value">1</div>
                            </div>
                        </div>
                    </div>
                    
                    {/* Spells Section - only shown for spellcasters */}
                    {characterData.spells && characterData.spells.hasSpellcasting && (
                        <div className="details-section">
                            <h3 className="section-title">Spells</h3>
                            
                            {/* Cantrips */}
                            {characterData.spells.cantrips && characterData.spells.cantrips.length > 0 && (
                                <div className="spell-group">
                                    <h4 className="spell-level-title">Cantrips</h4>
                                    <div className="spell-list">
                                        {characterData.spells.cantrips.map((spell, index) => (
                                            <div key={index} className="spell-item">
                                                <div className="spell-name">{spell.name}</div>
                                                <div className="spell-school">{spell.school}</div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                            
                            {/* 1st Level Spells */}
                            {characterData.spells.level1 && characterData.spells.level1.length > 0 && (
                                <div className="spell-group">
                                    <h4 className="spell-level-title">1st Level Spells</h4>
                                    <div className="spell-list">
                                        {characterData.spells.level1.map((spell, index) => (
                                            <div key={index} className="spell-item">
                                                <div className="spell-name">{spell.name}</div>
                                                <div className="spell-school">{spell.school}</div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                            
                            {(!characterData.spells.cantrips || characterData.spells.cantrips.length === 0) && 
                             (!characterData.spells.level1 || characterData.spells.level1.length === 0) && (
                                <div className="empty-message">No spells selected</div>
                            )}
                        </div>
                    )}
                    
                    {/* Racial Traits */}
                    <div className="details-section">
                        <h3 className="section-title">Racial Traits</h3>
                        <div className="traits-list">
                            {characterData.raceData?.traits?.map((trait, index) => (
                                <div key={index} className="trait-item">
                                    <div className="trait-name">{trait.name}</div>
                                    <div className="trait-description">{trait.description}</div>
                                </div>
                            ))}
                            
                            {/* Subrace traits if available */}
                            {characterData.raceData?.subraces?.map(subrace => {
                                if (subrace.id === characterData.subraceId && subrace.traits) {
                                    return subrace.traits.map((trait, index) => (
                                        <div key={`subrace-${index}`} className="trait-item subrace">
                                            <div className="trait-name">{trait.name}</div>
                                            <div className="trait-description">{trait.description}</div>
                                        </div>
                                    ));
                                }
                                return null;
                            })}
                            
                            {(!characterData.raceData?.traits || characterData.raceData.traits.length === 0) && (
                                <div className="empty-message">No racial traits</div>
                            )}
                        </div>
                    </div>
                    
                    {/* Background Features */}
                    <div className="details-section">
                        <h3 className="section-title">Background Feature</h3>
                        <div className="background-feature">
                            {characterData.backgroundFeature ? (
                                <>
                                    <div className="feature-name">{characterData.backgroundFeature.name}</div>
                                    <div className="feature-description">{characterData.backgroundFeature.description}</div>
                                </>
                            ) : (
                                <div className="empty-message">No background feature</div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
            
            {/* Action Buttons */}
            <div className="step10-navigation">
                <button className="back-button" onClick={prevStep}>
                    <i className="bi bi-arrow-left"></i> Back to Equipment
                </button>
                
                <div className="finalize-buttons">
                    <button 
                        className="save-play-button" 
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
                        className="save-button" 
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

export default Step10_ReviewFinalize;