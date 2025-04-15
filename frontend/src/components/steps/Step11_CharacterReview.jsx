// File: frontend/src/components/steps/Step11_CharacterReview.jsx

import React, { useState, useEffect } from 'react';
import './Step11_CharacterReview.css';

function Step11_CharacterReview({ characterData, updateCharacterData, prevStep }) {
    const [isSaving, setIsSaving] = useState(false);
    const [saveSuccess, setSaveSuccess] = useState(false);
    const [saveError, setSaveError] = useState(null);
    const [calculatedHP, setCalculatedHP] = useState(0);
    const [calculatedAC, setCalculatedAC] = useState(10);

    // Calculate derived stats on component mount
    useEffect(() => {
        // Calculate hit points based on class, constitution modifier, etc.
        calculateHitPoints();
        
        // Calculate armor class based on equipment, dexterity modifier, etc.
        calculateArmorClass();
    }, [characterData]);

    // Calculate hit points
    const calculateHitPoints = () => {
        let baseHP = 0;
        const constitutionMod = calculateAbilityModifier(characterData.finalAbilityScores.constitution);
        
        // Set base HP based on class hit die
        const classData = characterData.classData;
        if (classData && classData.hitDie) {
            // For first level, maximum hit die value + CON modifier
            switch (classData.hitDie) {
                case 'd6':
                    baseHP = 6;
                    break;
                case 'd8':
                    baseHP = 8;
                    break;
                case 'd10':
                    baseHP = 10;
                    break;
                case 'd12':
                    baseHP = 12;
                    break;
                default:
                    baseHP = 8; // Default to d8 if unknown
            }
        }
        
        // Add constitution modifier
        const totalHP = baseHP + constitutionMod;
        
        // Minimum of 1 hit point
        setCalculatedHP(Math.max(1, totalHP));
    };

    // Calculate armor class
    const calculateArmorClass = () => {
        // Base AC is 10 + DEX modifier
        const dexterityMod = calculateAbilityModifier(characterData.finalAbilityScores.dexterity);
        let baseAC = 10 + dexterityMod;
        
        // Check for equipped armor
        let hasArmor = false;
        let hasShield = false;
        
        if (characterData.equipment && characterData.equipment.equipped) {
            characterData.equipment.equipped.forEach(item => {
                // Check for armor
                if (item.type === 'armor' && !hasArmor) {
                    hasArmor = true;
                    // This is simplified. In reality, you'd need to look up the actual armor AC value
                    // and consider max dex modifier for certain armor types
                    if (item.item.toLowerCase().includes('leather')) {
                        baseAC = 11 + dexterityMod; // Leather armor is 11 + DEX
                    } else if (item.item.toLowerCase().includes('chain')) {
                        baseAC = 14 + Math.min(dexterityMod, 2); // Chain shirt is 14 + DEX (max 2)
                    } else if (item.item.toLowerCase().includes('plate')) {
                        baseAC = 18; // Plate is 18, no DEX bonus
                    }
                }
                
                // Check for shield
                if (item.type === 'shield' || item.item.toLowerCase().includes('shield')) {
                    hasShield = true;
                    baseAC += 2; // Shields add +2 AC
                }
            });
        }
        
        setCalculatedAC(baseAC);
    };

    // Calculate ability modifier
    const calculateAbilityModifier = (score) => {
        return Math.floor((score - 10) / 2);
    };

    // Format ability modifier display
    const formatModifier = (score) => {
        const modifier = calculateAbilityModifier(score);
        return modifier >= 0 ? `+${modifier}` : `${modifier}`;
    };

    // Get modifier CSS class
    const getModifierClass = (score) => {
        const modifier = calculateAbilityModifier(score);
        if (modifier > 0) return "positive";
        if (modifier < 0) return "negative";
        return "";
    };

    // Handle saving the character
    const handleSaveCharacter = (playImmediately = false) => {
        setIsSaving(true);
        setSaveSuccess(false);
        setSaveError(null);
        
        // Add calculated stats to character data
        const finalCharacterData = {
            ...characterData,
            hitPoints: calculatedHP,
            armorClass: calculatedAC,
            isDraft: false,
            submissionId: Date.now().toString(), // Used to prevent duplicate submissions
        };
        
        // Make API request to save the character
        fetch('/characters/api/save-character', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                // Add CSRF token from meta tag if using Flask
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content')
            },
            body: JSON.stringify(finalCharacterData)
        })
        .then(response => response.json())
        .then(data => {
            setIsSaving(false);
            
            if (data.success) {
                setSaveSuccess(true);
                
                // Redirect after successful save
                setTimeout(() => {
                    if (playImmediately) {
                        // Redirect to play game with this character
                        window.location.href = `/game/play/${data.character_id}`;
                    } else {
                        // Redirect to dashboard
                        window.location.href = '/game/dashboard';
                    }
                }, 1500);
            } else {
                setSaveError(data.error || "Failed to save character");
            }
        })
        .catch(error => {
            setIsSaving(false);
            setSaveError(`Error: ${error.message}`);
            console.error("Error saving character:", error);
        });
    };

    return (
        <div className="step11-outer-container">
            {/* Title */}
            <h2 className="step11-title">Character Review</h2>
            
            {/* Character name and basic info */}
            <h1 className="character-name">{characterData.characterName || "Unnamed Character"}</h1>
            <div className="character-subtitle">
                Level 1 {characterData.raceName} {characterData.className} • {characterData.backgroundName} • {characterData.alignmentName}
            </div>
            
            {/* Vital statistics (AC, HP) */}
            <div className="vital-stats-container">
                <div className="vital-stat">
                    <div className="ac-shield">
                        <div className="ac-value">{calculatedAC}</div>
                    </div>
                    <div className="vital-stat-label">Armor Class</div>
                </div>
                
                <div className="vital-stat">
                    <div className="hp-heart">
                        <div className="hp-value">{calculatedHP}</div>
                    </div>
                    <div className="vital-stat-label">Hit Points</div>
                </div>
            </div>
            
            {/* Ability Scores */}
            <div className="ability-scores-container">
                <div className="ability-score">
                    <div className="ability-name">STR</div>
                    <div className="ability-value">{characterData.finalAbilityScores?.strength || 10}</div>
                    <div className={`ability-modifier ${getModifierClass(characterData.finalAbilityScores?.strength || 10)}`}>
                        {formatModifier(characterData.finalAbilityScores?.strength || 10)}
                    </div>
                </div>
                <div className="ability-score">
                    <div className="ability-name">DEX</div>
                    <div className="ability-value">{characterData.finalAbilityScores?.dexterity || 10}</div>
                    <div className={`ability-modifier ${getModifierClass(characterData.finalAbilityScores?.dexterity || 10)}`}>
                        {formatModifier(characterData.finalAbilityScores?.dexterity || 10)}
                    </div>
                </div>
                <div className="ability-score">
                    <div className="ability-name">CON</div>
                    <div className="ability-value">{characterData.finalAbilityScores?.constitution || 10}</div>
                    <div className={`ability-modifier ${getModifierClass(characterData.finalAbilityScores?.constitution || 10)}`}>
                        {formatModifier(characterData.finalAbilityScores?.constitution || 10)}
                    </div>
                </div>
                <div className="ability-score">
                    <div className="ability-name">INT</div>
                    <div className="ability-value">{characterData.finalAbilityScores?.intelligence || 10}</div>
                    <div className={`ability-modifier ${getModifierClass(characterData.finalAbilityScores?.intelligence || 10)}`}>
                        {formatModifier(characterData.finalAbilityScores?.intelligence || 10)}
                    </div>
                </div>
                <div className="ability-score">
                    <div className="ability-name">WIS</div>
                    <div className="ability-value">{characterData.finalAbilityScores?.wisdom || 10}</div>
                    <div className={`ability-modifier ${getModifierClass(characterData.finalAbilityScores?.wisdom || 10)}`}>
                        {formatModifier(characterData.finalAbilityScores?.wisdom || 10)}
                    </div>
                </div>
                <div className="ability-score">
                    <div className="ability-name">CHA</div>
                    <div className="ability-value">{characterData.finalAbilityScores?.charisma || 10}</div>
                    <div className={`ability-modifier ${getModifierClass(characterData.finalAbilityScores?.charisma || 10)}`}>
                        {formatModifier(characterData.finalAbilityScores?.charisma || 10)}
                    </div>
                </div>
            </div>
            
            {/* Character Details Sections */}
            <div className="character-sections-container">
                {/* World & Campaign */}
                <div className="character-section">
                    <div className="section-header">
                        <i className="bi bi-globe section-icon"></i>
                        <h3 className="section-title">World & Campaign</h3>
                    </div>
                    <div className="section-content">
                        <ul>
                            <li>
                                <div className="item-name">World: {characterData.worldName}</div>
                            </li>
                            <li>
                                <div className="item-name">Campaign: {characterData.campaignName}</div>
                            </li>
                        </ul>
                    </div>
                </div>
                
                {/* Race & Background */}
                <div className="character-section">
                    <div className="section-header">
                        <i className="bi bi-person section-icon"></i>
                        <h3 className="section-title">Race & Background</h3>
                    </div>
                    <div className="section-content">
                        <ul>
                            <li>
                                <div className="item-name">Race: {characterData.raceName}</div>
                                {characterData.subraceName && (
                                    <div className="item-detail">Subrace: {characterData.subraceName}</div>
                                )}
                            </li>
                            <li>
                                <div className="item-name">Background: {characterData.backgroundName}</div>
                            </li>
                            <li>
                                <div className="item-name">Alignment: {characterData.alignmentName}</div>
                            </li>
                        </ul>
                    </div>
                </div>
                
                {/* Class & Features */}
                <div className="character-section">
                    <div className="section-header">
                        <i className="bi bi-shield section-icon"></i>
                        <h3 className="section-title">Class & Features</h3>
                    </div>
                    <div className="section-content">
                        <ul>
                            <li>
                                <div className="item-name">Class: {characterData.className}</div>
                                <div className="item-detail">Level: 1</div>
                            </li>
                            {characterData.classFeatures && (
                                <li>
                                    <div className="item-name">Class Features</div>
                                    <ul className="features-list">
                                        {characterData.classFeatures.standard?.map((feature, index) => (
                                            <li key={index}>{feature}</li>
                                        ))}
                                        {Object.entries(characterData.classFeatures.choices || {}).map(([feature, choiceId], index) => (
                                            <li key={`choice-${index}`}>{feature}: {choiceId}</li>
                                        ))}
                                    </ul>
                                </li>
                            )}
                        </ul>
                    </div>
                </div>
                
                {/* Spells (if applicable) */}
                {characterData.spells && characterData.spells.hasSpellcasting && (
                    <div className="character-section">
                        <div className="section-header">
                            <i className="bi bi-magic section-icon"></i>
                            <h3 className="section-title">Spellcasting</h3>
                        </div>
                        <div className="section-content">
                            <ul>
                                {characterData.spells.cantrips && characterData.spells.cantrips.length > 0 && (
                                    <li>
                                        <div className="item-name">Cantrips</div>
                                        <ul className="spells-list">
                                            {characterData.spells.cantrips.map((spell, index) => (
                                                <li key={index}>{spell.name}</li>
                                            ))}
                                        </ul>
                                    </li>
                                )}
                                
                                {characterData.spells.level1 && characterData.spells.level1.length > 0 && (
                                    <li>
                                        <div className="item-name">1st Level Spells</div>
                                        <ul className="spells-list">
                                            {characterData.spells.level1.map((spell, index) => (
                                                <li key={index}>{spell.name}</li>
                                            ))}
                                        </ul>
                                    </li>
                                )}
                            </ul>
                        </div>
                    </div>
                )}
                
                {/* Proficiencies */}
                {characterData.proficiencies && (
                    <div className="character-section">
                        <div className="section-header">
                            <i className="bi bi-tools section-icon"></i>
                            <h3 className="section-title">Proficiencies</h3>
                        </div>
                        <div className="section-content">
                            <ul>
                                <li>
                                    <div className="item-name">Skills</div>
                                    <ul className="proficiencies-list">
                                        {characterData.proficiencies.skills?.map((skill, index) => (
                                            <li key={index}>{skill}</li>
                                        ))}
                                    </ul>
                                </li>
                                {/* Add armor, weapon, tool proficiencies as needed */}
                            </ul>
                        </div>
                    </div>
                )}
                
                {/* Equipment */}
                {characterData.equipment && (
                    <div className="character-section">
                        <div className="section-header">
                            <i className="bi bi-bag section-icon"></i>
                            <h3 className="section-title">Equipment</h3>
                        </div>
                        <div className="section-content">
                            <ul>
                                {characterData.equipment.equipped?.map((item, index) => (
                                    <li key={index}>
                                        <div className="item-name">{item.item}</div>
                                        {item.type && <div className="item-detail">{item.type}</div>}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    </div>
                )}
            </div>
            
            {/* Save character buttons */}
            <div className="character-save-container">
                <h3>Ready to Begin Your Adventure?</h3>
                <p>Save your character to continue or return to the dashboard.</p>
                
                <div className="save-buttons">
                    <button
                        className="save-button"
                        onClick={() => handleSaveCharacter(false)}
                        disabled={isSaving}
                    >
                        {isSaving ? <span className="loading-indicator"></span> : <i className="bi bi-check-circle"></i>}
                        Save & Return to Dashboard
                    </button>
                    
                    <button
                        className="save-play-button"
                        onClick={() => handleSaveCharacter(true)}
                        disabled={isSaving}
                    >
                        {isSaving ? <span className="loading-indicator"></span> : <i className="bi bi-play-fill"></i>}
                        Save & Play Now
                    </button>
                </div>
                
                {saveSuccess && (
                    <div className="save-success visible">
                        Character saved successfully! Redirecting...
                    </div>
                )}
                
                {saveError && (
                    <div className="save-error visible">
                        {saveError}
                    </div>
                )}
            </div>
            
            {/* Navigation Buttons */}
            <div className="step11-navigation">
                <button className="back-button" onClick={prevStep}>
                    <i className="bi bi-arrow-left"></i> Back to Alignment
                </button>
            </div>
        </div>
    );
}

export default Step11_CharacterReview;