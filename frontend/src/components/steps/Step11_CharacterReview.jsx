// File: frontend/src/components/steps/Step11_CharacterReview.jsx

import React, { useState, useEffect } from 'react';
import './Step11_CharacterReview.css';

function Step11_CharacterReview({ characterData, updateCharacterData, prevStep }) {
    const [isLoading, setIsLoading] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState(null);
    const [successMessage, setSuccessMessage] = useState(null);
    
    // Calculate derived stats based on character data
    const [derivedStats, setDerivedStats] = useState({
        armorClass: 10,
        hitPoints: 0,
        initiative: 0
    });
    
    // Calculate vital stats based on character data
    useEffect(() => {
        // Calculate armor class
        let baseAC = 10;
        const dexModifier = calculateModifier(characterData.finalAbilityScores?.dexterity || 10);
        
        // Check for armor in equipment
        if (characterData.equipment && characterData.equipment.equipped) {
            // Find armor items
            const armorItems = characterData.equipment.equipped.filter(item => 
                item.type === 'armor' || item.type === 'shield'
            );
            
            // Apply armor bonuses
            armorItems.forEach(item => {
                if (item.details && item.details.armor_class) {
                    baseAC = item.details.armor_class;
                    
                    // Apply dex modifier with potential cap for medium/heavy armor
                    if (item.details.max_dex_bonus !== undefined) {
                        baseAC += Math.min(dexModifier, item.details.max_dex_bonus);
                    } else {
                        baseAC += dexModifier;
                    }
                }
                
                // Apply shield bonus
                if (item.details && item.details.armor_class_bonus) {
                    baseAC += item.details.armor_class_bonus;
                }
            });
        } else {
            // No armor found, just use 10 + dex modifier
            baseAC += dexModifier;
        }
        
        // Calculate hit points
        let baseHP = 0;
        
        // Get hit die from class data
        const hitDie = characterData.classData?.hitDie || 'd8';
        const hitDieValue = parseInt(hitDie.replace('d', ''));
        
        // At 1st level, characters get maximum hit points from their hit die
        baseHP = hitDieValue;
        
        // Add Constitution modifier
        const conModifier = calculateModifier(characterData.finalAbilityScores?.constitution || 10);
        baseHP += conModifier;
        
        // Ensure minimum of 1 hit point
        baseHP = Math.max(1, baseHP);
        
        // Calculate initiative (just Dex modifier)
        const initiative = dexModifier;
        
        setDerivedStats({
            armorClass: baseAC,
            hitPoints: baseHP,
            initiative: initiative
        });
    }, [characterData]);
    
    // Helper function to calculate ability modifier
    const calculateModifier = (score) => {
        return Math.floor((score - 10) / 2);
    };
    
    // Format ability modifier with + or - sign
    const formatModifier = (score) => {
        const modifier = calculateModifier(score);
        return modifier >= 0 ? `+${modifier}` : `${modifier}`;
    };
    
    // Handle saving the character
    const handleSaveCharacter = async () => {
        setIsSaving(true);
        setError(null);
        
        try {
            // Add submission ID to prevent duplicate saves
            const submissionId = Date.now().toString();
            
            const characterToSave = {
                ...characterData,
                submissionId,
                isDraft: false, // Mark as complete (not a draft)
                createdAt: new Date().toISOString(),
                updatedAt: new Date().toISOString(),
                completedAt: new Date().toISOString()
            };
            
            // Send the request
            const response = await fetch('/characters/api/save-character', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
                },
                body: JSON.stringify(characterToSave)
            });
            
            const data = await response.json();
            
            if (data.success) {
                setSuccessMessage('Character saved successfully!');
                
                // Wait a moment before redirecting
                setTimeout(() => {
                    window.location.href = '/characters/dashboard';
                }, 1500);
            } else {
                throw new Error(data.error || 'Failed to save character');
            }
        } catch (err) {
            console.error('Error saving character:', err);
            setError(`Error: ${err.message}`);
        } finally {
            setIsSaving(false);
        }
    };
    
    // Handle play button (save and start game)
    const handlePlayNow = async () => {
        setIsSaving(true);
        setError(null);
        
        try {
            // Add submission ID to prevent duplicate saves
            const submissionId = Date.now().toString();
            
            const characterToSave = {
                ...characterData,
                submissionId,
                isDraft: false, // Mark as complete (not a draft)
                createdAt: new Date().toISOString(),
                updatedAt: new Date().toISOString(),
                completedAt: new Date().toISOString()
            };
            
            // Send the request
            const response = await fetch('/characters/api/save-character', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
                },
                body: JSON.stringify(characterToSave)
            });
            
            const data = await response.json();
            
            if (data.success) {
                setSuccessMessage('Character saved! Starting game...');
                
                // Wait a moment before redirecting to play
                setTimeout(() => {
                    window.location.href = `/game/play/${data.character_id}`;
                }, 1500);
            } else {
                throw new Error(data.error || 'Failed to save character');
            }
        } catch (err) {
            console.error('Error saving character for play:', err);
            setError(`Error: ${err.message}`);
        } finally {
            setIsSaving(false);
        }
    };
    
    if (isLoading) {
        return (
            <div className="loading-container">
                <div className="spinner-border" role="status"></div>
                <div>Loading Character Data...</div>
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
        <div className="step11-outer-container">
            {/* Title */}
            <h2 className="step11-title">Character Review</h2>
            
            {/* Loading overlay when saving */}
            {isSaving && (
                <div className="loading-overlay">
                    <div className="loading-spinner"></div>
                    <div className="loading-text">
                        {successMessage || 'Saving your character...'}
                    </div>
                </div>
            )}
            
            {/* Character Name and Basic Info */}
            <div className="vital-stats-container">
                <h1 className="character-name-display">{characterData.characterName || 'Unnamed Character'}</h1>
                
                <div className="character-subtitle">
                    Level 1 {characterData.raceName} {characterData.className} • {characterData.backgroundName} • {characterData.alignmentName}
                </div>
                
                {/* Vital Stats Display */}
                <div className="vital-stats-grid">
                    {/* Hit Points */}
                    <div className="hit-points-container">
                        <div className="hit-points-heart">
                            <span className="hit-points-value">{derivedStats.hitPoints}</span>
                        </div>
                        <div className="hit-points-label">Hit Points</div>
                    </div>
                    
                    {/* Armor Class */}
                    <div className="armor-class-container">
                        <div className="armor-class-shield">
                            <span className="armor-class-value">{derivedStats.armorClass}</span>
                        </div>
                        <div className="armor-class-label">Armor Class</div>
                    </div>
                    
                    {/* Initiative */}
                    <div className="initiative-container">
                        <div className="initiative-circle">
                            <span className="initiative-value">
                                {derivedStats.initiative >= 0 ? `+${derivedStats.initiative}` : derivedStats.initiative}
                            </span>
                        </div>
                        <div className="initiative-label">Initiative</div>
                    </div>
                </div>
            </div>
            
            {/* Ability Scores */}
            <div className="ability-scores-container">
                <h3 className="section-title">Ability Scores</h3>
                
                <div className="abilities-grid">
                    {characterData.finalAbilityScores && Object.entries(characterData.finalAbilityScores).map(([ability, score]) => {
                        const modifier = calculateModifier(score);
                        return (
                            <div className="ability-box" key={ability}>
                                <div className="ability-name">{ability.charAt(0).toUpperCase() + ability.slice(1)}</div>
                                <div className="ability-score">{score}</div>
                                <div className={`ability-modifier ${modifier < 0 ? 'negative' : ''}`}>
                                    {formatModifier(score)}
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
            
            {/* Character Details */}
            <div className="character-details-container">
                <h3 className="section-title">Character Details</h3>
                
                <div className="details-grid">
                    {/* World */}
                    <div className="detail-card">
                        <div className="detail-title">World</div>
                        <div className="detail-value">{characterData.worldName || 'Unknown'}</div>
                    </div>
                    
                    {/* Campaign */}
                    <div className="detail-card">
                        <div className="detail-title">Campaign</div>
                        <div className="detail-value">{characterData.campaignName || 'Custom Campaign'}</div>
                    </div>
                    
                    {/* Alignment */}
                    <div className="detail-card">
                        <div className="detail-title">Alignment</div>
                        <div className="detail-value">{characterData.alignmentName || 'Unaligned'}</div>
                    </div>
                    
                    {/* Class */}
                    <div className="detail-card">
                        <div className="detail-title">Class</div>
                        <div className="detail-value">{characterData.className || 'Unknown'}</div>
                    </div>
                    
                    {/* Race */}
                    <div className="detail-card">
                        <div className="detail-title">Race</div>
                        <div className="detail-value">
                            {characterData.raceName || 'Unknown'}
                            {characterData.subraceName && ` (${characterData.subraceName})`}
                        </div>
                    </div>
                    
                    {/* Background */}
                    <div className="detail-card">
                        <div className="detail-title">Background</div>
                        <div className="detail-value">{characterData.backgroundName || 'Unknown'}</div>
                    </div>
                </div>
            </div>
            
            {/* Secondary Details (Features, Equipment, etc.) */}
            <div className="secondary-details-container">
                {/* Class Features */}
                <div className="features-container">
                    <h3 className="section-title">Class Features</h3>
                    
                    <div className="features-list">
                        {/* Standard Features */}
                        {characterData.classFeatures?.standard && (
                            <>
                                <h4 className="section-subtitle">Standard Features</h4>
                                {characterData.classFeatures.standard.map((feature, index) => (
                                    <div className="feature-item" key={index}>
                                        <div className="feature-name">{feature}</div>
                                    </div>
                                ))}
                            </>
                        )}
                        
                        {/* Choice Features */}
                        {characterData.classFeatures?.choices && Object.entries(characterData.classFeatures.choices).length > 0 && (
                            <>
                                <h4 className="section-subtitle">Selected Features</h4>
                                {Object.entries(characterData.classFeatures.choices).map(([feature, choiceId], index) => (
                                    <div className="feature-item" key={index}>
                                        <div className="feature-name">{feature}: {choiceId}</div>
                                    </div>
                                ))}
                            </>
                        )}
                        
                        {/* If no features */}
                        {(!characterData.classFeatures?.standard || characterData.classFeatures.standard.length === 0) && 
                         (!characterData.classFeatures?.choices || Object.entries(characterData.classFeatures.choices).length === 0) && (
                            <div className="feature-item">
                                <div className="feature-name">No class features available</div>
                            </div>
                        )}
                    </div>
                </div>
                
                {/* Equipment */}
                <div className="equipment-container">
                    <h3 className="section-title">Equipment</h3>
                    
                    <div className="equipment-list">
                        {characterData.equipment?.equipped && characterData.equipment.equipped.length > 0 ? (
                            characterData.equipment.equipped.map((item, index) => (
                                <div className="equipment-item" key={index}>
                                    <div className="equipment-name">
                                        {item.item || item.name || "Unknown Item"}
                                    </div>
                                    {item.type && (
                                        <div className="equipment-type">{item.type}</div>
                                    )}
                                </div>
                            ))
                        ) : (
                            <div className="equipment-item">
                                <div className="equipment-name">No equipment available</div>
                            </div>
                        )}
                    </div>
                </div>
                
                {/* Proficiencies */}
                <div className="proficiencies-container">
                    <h3 className="section-title">Proficiencies</h3>
                    
                    <div className="proficiencies-list">
                        {/* Skills */}
                        {characterData.proficiencies?.skills && characterData.proficiencies.skills.length > 0 && (
                            <>
                                <h4 className="section-subtitle">Skills</h4>
                                {characterData.proficiencies.skills.map((skill, index) => (
                                    <div className="proficiency-item" key={index}>
                                        <div className="proficiency-name">{skill}</div>
                                    </div>
                                ))}
                            </>
                        )}
                        
                        {/* If no proficiencies */}
                        {(!characterData.proficiencies?.skills || characterData.proficiencies.skills.length === 0) && (
                            <div className="proficiency-item">
                                <div className="proficiency-name">No proficiencies available</div>
                            </div>
                        )}
                    </div>
                </div>
                
                {/* Spells (if applicable) */}
                {characterData.spells?.hasSpellcasting && (
                    <div className="spells-container">
                        <h3 className="section-title">Spells</h3>
                        
                        <div className="spells-list">
                            {/* Cantrips */}
                            {characterData.spells.cantrips && characterData.spells.cantrips.length > 0 && (
                                <>
                                    <h4 className="section-subtitle">Cantrips</h4>
                                    {characterData.spells.cantrips.map((spell, index) => (
                                        <div className="spell-item" key={index}>
                                            <div className="spell-name">{spell.name}</div>
                                            <div className="spell-level">Cantrip</div>
                                        </div>
                                    ))}
                                </>
                            )}
                            
                            {/* 1st Level Spells */}
                            {characterData.spells.level1 && characterData.spells.level1.length > 0 && (
                                <>
                                    <h4 className="section-subtitle">1st Level Spells</h4>
                                    {characterData.spells.level1.map((spell, index) => (
                                        <div className="spell-item" key={index}>
                                            <div className="spell-name">{spell.name}</div>
                                            <div className="spell-level">1st Level</div>
                                        </div>
                                    ))}
                                </>
                            )}
                            
                            {/* If no spells */}
                            {(!characterData.spells.cantrips || characterData.spells.cantrips.length === 0) && 
                             (!characterData.spells.level1 || characterData.spells.level1.length === 0) && (
                                <div className="spell-item">
                                    <div className="spell-name">No spells available</div>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
            
            {/* Action Buttons */}
            <div className="action-buttons-container">
                <button className="save-button" onClick={handleSaveCharacter} disabled={isSaving}>
                    <i className="bi bi-save"></i> Save Character
                </button>
                
                <button className="play-button" onClick={handlePlayNow} disabled={isSaving}>
                    <i className="bi bi-play-fill"></i> Save & Play Now
                </button>
            </div>
            
            {/* Back Button */}
            <div className="step11-navigation">
                <button className="back-button" onClick={prevStep}>
                    <i className="bi bi-arrow-left"></i> Back to Alignment
                </button>
            </div>
        </div>
    );
}

export default Step11_CharacterReview;