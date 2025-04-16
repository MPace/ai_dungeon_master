// File: frontend/src/components/steps/Step2_6_PremadeCharacterSelector.jsx

import React, { useState, useEffect, useRef } from 'react';
import './Step2_6_PremadeCharacterSelector.css';

function Step2_6_PremadeCharacterSelector({ characterData, updateCharacterData, nextStep, prevStep }) {
    const [premadeCharacters, setPremadeCharacters] = useState([]);
    const [selectedCharacter, setSelectedCharacter] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const [activeDetails, setActiveDetails] = useState(null);
    
    // Ref for character details modal
    const detailsModalRef = useRef(null);

    // Fetch premade characters on component mount
    useEffect(() => {
        setIsLoading(true);
        setError(null);
        
        // Fetch data from the API
        fetch(`/characters/api/premade-characters/${characterData.worldId}`)
            .then(response => {
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                return response.json();
            })
            .then(data => {
                if (data.success && data.characters) {
                    console.log("Premade characters loaded:", data.characters);
                    setPremadeCharacters(data.characters);
                } else {
                    throw new Error(data.error || 'Failed to load premade characters');
                }
                setIsLoading(false);
            })
            .catch(err => {
                console.error("Failed to fetch premade characters:", err);
                setError(`Failed to load premade characters: ${err.message}`);
                setIsLoading(false);
            });
    }, [characterData.worldId]);

    // Handler for character selection
    const handleSelectCharacter = (character) => {
        setSelectedCharacter(character);
        setActiveDetails(character);
        
        // Add a slight delay before adding the active class for animation
        setTimeout(() => {
            if (detailsModalRef.current) {
                detailsModalRef.current.classList.add('active');
            }
        }, 10);
    };

    // Handler for closing character details
    const handleCloseDetails = () => {
        if (detailsModalRef.current) {
            detailsModalRef.current.classList.remove('active');
            
            // Wait for animation to complete before removing modal
            setTimeout(() => {
                setActiveDetails(null);
            }, 400);
        } else {
            setActiveDetails(null);
        }
    };

    // Handler for continuing with selected character
    const handleContinue = () => {
        if (!selectedCharacter) {
            alert("Please select a character first");
            return;
        }
        
        // Update character data with selected premade character
        updateCharacterData({
            isPremadeCharacter: true,
            premadeCharacterId: selectedCharacter.id,
            characterName: selectedCharacter.name,
            raceName: selectedCharacter.race,
            className: selectedCharacter.class,
            backgroundName: selectedCharacter.background,
            alignment: selectedCharacter.alignment,
            alignmentName: selectedCharacter.alignment,
            gender: selectedCharacter.gender,
            description: selectedCharacter.description,
            finalAbilityScores: selectedCharacter.abilities,
            classFeatures: selectedCharacter.classFeatures,
            proficiencies: {
                skills: selectedCharacter.proficiencies.skills
            },
            equipment: {
                equipped: selectedCharacter.equipment.equipped
            },
            backgroundFeature: selectedCharacter.backgroundFeature,
            spells: selectedCharacter.spells || { hasSpellcasting: false }
        });
        
        // Skip to Step 11 (Review)
        // We'll need to modify the CharacterCreator component to handle this
        nextStep(true);
    };

    // Calculate ability modifier with sign
    const getModifier = (score) => {
        const modifier = Math.floor((score - 10) / 2);
        return modifier >= 0 ? `+${modifier}` : `${modifier}`;
    };

    // Render loading state
    if (isLoading) {
        return (
            <div className="loading-container">
                <div className="spinner-border" role="status"></div>
                <div>Loading Premade Characters...</div>
            </div>
        );
    }

    // Render error state
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
        <div className="premade-character-selector-container">
            <h2 className="premade-character-title">Choose a Premade Character</h2>
            <p className="premade-character-description">
                Select from these ready-to-play characters designed for new players.
            </p>
            
            {/* Character Grid */}
            <div className="premade-character-grid">
                {premadeCharacters.map((character) => (
                    <div 
                        key={character.id}
                        className={`premade-character-card ${selectedCharacter?.id === character.id ? 'selected' : ''}`}
                        onClick={() => handleSelectCharacter(character)}
                    >
                        <div className="premade-character-image-container">
                            <img 
                                src={character.image} 
                                alt={character.name} 
                                className="premade-character-image"
                                onError={(e) => {
                                    e.target.src = '/images/characters/default.jpg'; 
                                    e.target.onerror = null;
                                }}
                            />
                        </div>
                        <div className="premade-character-info">
                            <h3 className="premade-character-name">{character.name}</h3>
                            <div className="premade-character-basics">
                                <span>{character.race}</span> • 
                                <span>{character.class}</span> • 
                                <span>Level {character.level}</span>
                            </div>
                            <p className="premade-character-short-desc">
                                {character.description.substring(0, 100)}...
                            </p>
                        </div>
                        <div className="premade-character-select-btn">
                            View Details
                        </div>
                    </div>
                ))}
                
                {premadeCharacters.length === 0 && (
                    <div className="no-characters-message">
                        <i className="bi bi-exclamation-circle"></i>
                        <p>No premade characters found for this world.</p>
                    </div>
                )}
            </div>
            
            {/* Character Details Modal */}
            {activeDetails && (
                <div 
                    className="character-details-overlay" 
                    ref={detailsModalRef} 
                    onClick={handleCloseDetails}
                >
                    <div className="character-details-modal" onClick={(e) => e.stopPropagation()}>
                        <button className="close-button" onClick={handleCloseDetails}>×</button>
                        
                        <div className="character-details-content">
                            <div className="character-details-header">
                                <div className="character-portrait-container">
                                    <img 
                                        src={activeDetails.image} 
                                        alt={activeDetails.name} 
                                        className="character-portrait"
                                        onError={(e) => {
                                            e.target.src = '/images/characters/default.jpg'; 
                                            e.target.onerror = null;
                                        }}
                                    />
                                </div>
                                
                                <div className="character-details-identity">
                                    <h2 className="character-details-name">{activeDetails.name}</h2>
                                    <div className="character-details-specs">
                                        <span>{activeDetails.race}</span> • 
                                        <span>{activeDetails.class}</span> • 
                                        <span>Level {activeDetails.level}</span>
                                    </div>
                                    <div className="character-details-alignment">{activeDetails.alignment}</div>
                                    <div className="character-details-background">{activeDetails.background}</div>
                                </div>
                            </div>
                            
                            <div className="character-details-description">
                                <h3>Description</h3>
                                <p>{activeDetails.description}</p>
                            </div>
                            
                            <div className="character-details-abilities">
                                <h3>Ability Scores</h3>
                                <div className="ability-scores-container">
                                    {Object.entries(activeDetails.abilities).map(([ability, score]) => (
                                        <div key={ability} className="ability-score-item">
                                            <div className="ability-name">{ability.substring(0, 3).toUpperCase()}</div>
                                            <div className="ability-value">{score}</div>
                                            <div className="ability-modifier">{getModifier(score)}</div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                            
                            <div className="character-details-proficiencies">
                                <h3>Proficiencies</h3>
                                <div className="proficiency-group">
                                    <h4>Skills</h4>
                                    <div className="proficiency-items">
                                        {activeDetails.proficiencies.skills.map((skill, index) => (
                                            <span key={index} className="proficiency-tag">{skill}</span>
                                        ))}
                                    </div>
                                </div>
                                
                                {activeDetails.proficiencies.languages && (
                                    <div className="proficiency-group">
                                        <h4>Languages</h4>
                                        <div className="proficiency-items">
                                            {activeDetails.proficiencies.languages.map((language, index) => (
                                                <span key={index} className="proficiency-tag">{language}</span>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                            
                            <div className="character-details-features">
                                <h3>Features & Traits</h3>
                                
                                {/* Class Features */}
                                <div className="feature-group">
                                    <h4>Class Features</h4>
                                    <ul className="feature-list">
                                        {activeDetails.classFeatures.standard.map((feature, index) => (
                                            <li key={index}>{feature}</li>
                                        ))}
                                    </ul>
                                </div>
                                
                                {/* Racial Traits */}
                                <div className="feature-group">
                                    <h4>Racial Traits</h4>
                                    <ul className="feature-list">
                                        {activeDetails.racialTraits.map((trait, index) => (
                                            <li key={index}>{trait}</li>
                                        ))}
                                    </ul>
                                </div>
                                
                                {/* Background Feature */}
                                <div className="feature-group">
                                    <h4>Background Feature</h4>
                                    <div className="background-feature">
                                        <div className="background-feature-name">{activeDetails.backgroundFeature.name}</div>
                                        <p>{activeDetails.backgroundFeature.description}</p>
                                    </div>
                                </div>
                            </div>
                            
                            <div className="character-details-equipment">
                                <h3>Equipment</h3>
                                <ul className="equipment-list">
                                    {activeDetails.equipment.equipped.map((item, index) => (
                                        <li key={index}>
                                            {item.item}
                                            {item.type && <span className="equipment-type">{item.type}</span>}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                            
                            <div className="choose-character-container">
                                <button 
                                    className="choose-character-btn"
                                    onClick={handleContinue}
                                >
                                    Choose {activeDetails.name}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
            
            {/* Navigation Buttons */}
            <div className="premade-character-navigation">
                <button className="back-button" onClick={prevStep}>
                    <i className="bi bi-arrow-left"></i> Back to Character Type
                </button>
                
                <button 
                    className={`continue-button ${selectedCharacter ? 'active' : ''}`}
                    onClick={handleContinue}
                    disabled={!selectedCharacter}
                >
                    Continue to Review <i className="bi bi-arrow-right"></i>
                </button>
            </div>
        </div>
    );
}

export default Step2_6_PremadeCharacterSelector;