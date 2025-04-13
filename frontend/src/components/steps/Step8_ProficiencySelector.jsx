// File: frontend/src/components/steps/Step8_ProficiencySelector.jsx

import React, { useState, useEffect, useRef } from 'react';
import './Step8_ProficiencySelector.css';

function Step8_ProficiencySelector({ characterData, updateCharacterData, nextStep, prevStep }) {
    const [availableSkills, setAvailableSkills] = useState([]);
    const [selectedSkills, setSelectedSkills] = useState([]);
    const [backgroundSkills, setBackgroundSkills] = useState([]);
    const [maxSkillChoices, setMaxSkillChoices] = useState(0);
    const [skillDescriptions, setSkillDescriptions] = useState({});
    const [activeSkillDetails, setActiveSkillDetails] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    
    // Ref for skill details modal
    const skillDetailsRef = useRef(null);

    // Fetch proficiency data
    useEffect(() => {
        if (!characterData.worldId || !characterData.classId) {
            setError("Missing required character data. Please complete previous steps.");
            setIsLoading(false);
            return;
        }

        setIsLoading(true);
        setError(null);
        
        // Fetch data from the API
        fetch(`/characters/api/creation-data/${characterData.worldId}`)
            .then(response => {
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                return response.json();
            })
            .then(data => {
                if (data.success && data.data) {
                    console.log("Creation data received:", data.data);
                    
                    // Find the class data for the selected class
                    const selectedClass = data.data.classes.find(c => c.id === characterData.classId);
                    
                    if (selectedClass) {
                        // Get skill choices and max count
                        const classSkills = selectedClass.skillChoices || [];
                        const classSkillCount = selectedClass.skillCount || 0;
                        
                        setAvailableSkills(classSkills);
                        setMaxSkillChoices(classSkillCount);
                        
                        // Get background skills if available
                        if (characterData.backgroundId) {
                            const selectedBackground = data.data.backgrounds.find(b => b.id === characterData.backgroundId);
                            if (selectedBackground && selectedBackground.skillProficiencies) {
                                setBackgroundSkills(selectedBackground.skillProficiencies);
                            }
                        }
                        
                        // Get skill descriptions from the API data
                        if (data.data.proficiencies && data.data.proficiencies.skills) {
                            const skillData = {};
                            
                            // Transform the data structure to match our component's needs
                            Object.entries(data.data.proficiencies.skills).forEach(([key, value]) => {
                                skillData[value.name] = {
                                    ability: value.ability,
                                    description: value.description,
                                    examples: value.examples
                                };
                            });
                            
                            setSkillDescriptions(skillData);
                        } else {
                            throw new Error("Proficiency data not found in API response");
                        }
                        
                        setIsLoading(false);
                    } else {
                        throw new Error(`Class ${characterData.classId} not found in data.`);
                    }
                } else {
                    throw new Error(data.error || 'Invalid data format.');
                }
            })
            .catch(err => {
                console.error("Step8: Failed to fetch proficiency data:", err);
                setError(`Failed to load proficiency data: ${err.message}. Check your connection or try again later.`);
                setIsLoading(false);
            });
    }, [characterData.worldId, characterData.classId, characterData.backgroundId]);

    // Handler for selecting a skill
    const handleSkillSelect = (skill) => {
        // Check if the skill is already from background
        if (backgroundSkills.includes(skill)) {
            return; // Cannot toggle background skills
        }
        
        // Toggle selection
        if (selectedSkills.includes(skill)) {
            setSelectedSkills(prev => prev.filter(s => s !== skill));
        } else {
            // Check if at maximum
            if (selectedSkills.length < maxSkillChoices) {
                setSelectedSkills(prev => [...prev, skill]);
            } else {
                alert(`You can only select ${maxSkillChoices} skills from your class.`);
            }
        }
    };

    // Handler for showing skill details
    const handleShowDetails = (skill) => {
        setActiveSkillDetails({
            name: skill,
            ...skillDescriptions[skill]
        });
        
        // Add a slight delay before adding the active class for animation
        setTimeout(() => {
            if (skillDetailsRef.current) {
                skillDetailsRef.current.classList.add('active');
            }
        }, 10);
    };

    // Handler for closing skill details
    const handleCloseDetails = () => {
        if (skillDetailsRef.current) {
            skillDetailsRef.current.classList.remove('active');
            
            // Wait for animation to complete before removing modal
            setTimeout(() => {
                setActiveSkillDetails(null);
            }, 400);
        } else {
            setActiveSkillDetails(null);
        }
    };

    // Validate skill selections
    const validateSelections = () => {
        if (selectedSkills.length < maxSkillChoices) {
            return {
                valid: false,
                message: `Please select ${maxSkillChoices - selectedSkills.length} more skill(s).`
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
        
        // Combine selected skills with background skills
        const allSkills = [...new Set([...selectedSkills, ...backgroundSkills])];
        
        // Update character data with selected skills
        updateCharacterData({
            proficiencies: {
                skills: allSkills,
                classSkills: selectedSkills,
                backgroundSkills: backgroundSkills
            }
        });
        
        // Move to next step
        nextStep();
    };

    // Get ability modifier text
    const getAbilityModifier = (ability) => {
        if (!characterData.finalAbilityScores) return null;
        
        const abilityScore = characterData.finalAbilityScores[ability.toLowerCase()];
        if (!abilityScore) return null;
        
        const modifier = Math.floor((abilityScore - 10) / 2);
        return modifier >= 0 ? `+${modifier}` : `${modifier}`;
    };

    // --- Render Logic ---
    if (isLoading) {
        return (
            <div className="loading-container">
                <div className="spinner-border" role="status"></div>
                <div>Loading Proficiency Options...</div>
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
        <div className="step8-outer-container">
            {/* Title */}
            <h2 className="step8-title">Skill Proficiencies</h2>
            
            {/* Proficiency Selection Explanation */}
            <div className="proficiency-explanation">
                <h3>Choose Your Skills</h3>
                <p>
                    Skill proficiencies represent your character's training and aptitude in various abilities.
                    When making an ability check in a skill you're proficient with, you add your proficiency bonus to the roll.
                </p>
                <p>
                    Your class ({characterData.className}) allows you to choose <strong>{maxSkillChoices}</strong> skills from the options below.
                    {backgroundSkills.length > 0 && ` Your background (${characterData.backgroundName}) already gives you proficiency in ${backgroundSkills.join(' and ')}.`}
                </p>
                <div className="selection-counter">
                    Selected: <span className={selectedSkills.length === maxSkillChoices ? 'complete' : ''}>{selectedSkills.length}/{maxSkillChoices}</span>
                </div>
            </div>
            
            {/* Skill Selection Grid */}
            <div className="skill-selection-container">
                <div className="skill-grid">
                    {availableSkills.map((skill) => {
                        const isFromBackground = backgroundSkills.includes(skill);
                        const isSelected = selectedSkills.includes(skill) || isFromBackground;
                        const abilityInfo = skillDescriptions[skill];
                        const abilityName = abilityInfo ? abilityInfo.ability : '';
                        const abilityMod = getAbilityModifier(abilityName);
                        
                        return (
                            <div 
                                key={skill} 
                                className={`skill-card ${isSelected ? 'selected' : ''} ${isFromBackground ? 'background-skill' : ''}`}
                                onClick={() => handleSkillSelect(skill)}
                            >
                                <div className="skill-header">
                                    <h3 className="skill-name">{skill}</h3>
                                    <div className="skill-ability">
                                        {abilityName}
                                        {abilityMod && <span className="ability-mod">{abilityMod}</span>}
                                    </div>
                                </div>
                                
                                <p className="skill-short-desc">
                                    {skillDescriptions[skill]?.description.substring(0, 120)}...
                                </p>
                                
                                <div className="skill-footer">
                                    <button 
                                        className="details-button"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            handleShowDetails(skill);
                                        }}
                                    >
                                        See Details
                                    </button>
                                    
                                    {isFromBackground && (
                                        <div className="from-background">
                                            From {characterData.backgroundName}
                                        </div>
                                    )}
                                </div>
                                
                                <div className="selected-indicator">
                                    <i className="bi bi-check-circle-fill"></i> Selected
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
            
            {/* Skill Details Modal */}
            {activeSkillDetails && (
                <div 
                    className="skill-details-overlay" 
                    ref={skillDetailsRef} 
                    onClick={handleCloseDetails}
                >
                    <div className="skill-details-modal" onClick={(e) => e.stopPropagation()}>
                        <button className="close-button" onClick={handleCloseDetails}>×</button>
                        
                        <div className="skill-details-header">
                            <h3 className="skill-details-name">{activeSkillDetails.name}</h3>
                            <div className="skill-details-ability">
                                {activeSkillDetails.ability} Skill
                                {characterData.finalAbilityScores && (
                                    <span className="ability-score-value">
                                        {" "}(Score: {characterData.finalAbilityScores[activeSkillDetails.ability.toLowerCase()]}, 
                                        Modifier: {getAbilityModifier(activeSkillDetails.ability)})
                                    </span>
                                )}
                            </div>
                        </div>
                        
                        <div className="skill-details-content">
                            <div className="skill-details-description">
                                <h4>Description</h4>
                                <p>{activeSkillDetails.description}</p>
                            </div>
                            
                            <div className="skill-details-examples">
                                <h4>Common Uses</h4>
                                <p>{activeSkillDetails.examples}</p>
                            </div>
                            
                            <div className="skill-details-mechanics">
                                <h4>Game Mechanics</h4>
                                <p>
                                    When you make a {activeSkillDetails.name} check, you roll a d20 and add your {activeSkillDetails.ability} modifier 
                                    {selectedSkills.includes(activeSkillDetails.name) || backgroundSkills.includes(activeSkillDetails.name)
                                        ? " plus your proficiency bonus, which is +2 at 1st level."
                                        : ". If you gain proficiency in this skill, you will also add your proficiency bonus."}
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            )}
            
            {/* Validation message */}
            {selectedSkills.length < maxSkillChoices && (
                <div className="validation-message">
                    Please select {maxSkillChoices - selectedSkills.length} more skill(s).
                </div>
            )}
            
            {/* Navigation Buttons */}
            <div className="step8-navigation">
                <button className="back-button" onClick={prevStep}>
                    <i className="bi bi-arrow-left"></i> Back
                </button>
                
                <button 
                    className={`continue-button ${validateSelections().valid ? 'active' : ''}`}
                    onClick={handleContinue}
                    disabled={!validateSelections().valid}
                >
                    Continue <i className="bi bi-arrow-right"></i>
                </button>
            </div>
        </div>
    );
}

export default Step8_ProficiencySelector;