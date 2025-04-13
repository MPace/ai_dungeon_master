// File: frontend/src/components/steps/Step6_ClassFeatures.jsx

import React, { useState, useEffect, useCallback, useRef } from 'react';
import './Step6_ClassFeatures.css';

function Step6_ClassFeatures({ characterData, updateCharacterData, nextStep, prevStep }) {
    const [classFeatures, setClassFeatures] = useState([]);
    const [requiredFeatures, setRequiredFeatures] = useState([]);
    const [optionalFeatures, setOptionalFeatures] = useState([]);
    const [selectedChoices, setSelectedChoices] = useState({});
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showFeatureDetails, setShowFeatureDetails] = useState(null);
    
    // Ref for feature details modal
    const featureDetailsRef = useRef(null);

    // Fetch class features data
    useEffect(() => {
        if (!characterData.classId) {
            setError("No class selected. Please go back to Step 3.");
            setIsLoading(false);
            return;
        }

        setIsLoading(true);
        setError(null);
        
        // Fetch data from the API using the world and class ID
        fetch(`/characters/api/creation-data/${characterData.worldId}`)
            .then(response => {
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                return response.json();
            })
            .then(data => {
                if (data.success && data.data) {
                    console.log("Class data received:", data.data);
                    
                    // Find the class data for the selected class
                    const selectedClass = data.data.classes.find(c => c.id === characterData.classId);
                    
                    if (selectedClass && selectedClass.features && selectedClass.features.level1) {
                        console.log("Class features found:", selectedClass.features.level1);
                        
                        // Set class features
                        setClassFeatures(selectedClass.features.level1);
                        
                        // Split features into required and optional
                        if (selectedClass.features.level1.required) {
                            setRequiredFeatures(selectedClass.features.level1.required);
                        }
                        
                        if (selectedClass.features.level1.optional) {
                            setOptionalFeatures(selectedClass.features.level1.optional);
                        }
                        
                        // Initialize selected choices with empty values
                        const initialChoices = {};
                        if (selectedClass.features.level1.optional) {
                            selectedClass.features.level1.optional.forEach(feature => {
                                if (feature.type === 'choice') {
                                    initialChoices[feature.id] = null;
                                }
                            });
                        }
                        setSelectedChoices(initialChoices);
                        
                        setIsLoading(false);
                    } else {
                        throw new Error(`No features found for class: ${characterData.classId}`);
                    }
                } else {
                    throw new Error(data.error || 'Invalid data format.');
                }
            })
            .catch(err => {
                console.error("Step6: Failed to fetch class features:", err);
                setError(`Failed to load class features: ${err.message}. Check your connection or try again later.`);
                setIsLoading(false);
            });
    }, [characterData.classId, characterData.worldId]);

    // Handler for selecting a choice
    const handleChoiceSelect = (featureId, choiceId) => {
        setSelectedChoices(prev => ({
            ...prev,
            [featureId]: choiceId
        }));
    };

    // Handler for showing feature details
    const handleShowDetails = (feature) => {
        setShowFeatureDetails(feature);
        
        // Add a slight delay before adding the active class for animation
        setTimeout(() => {
            if (featureDetailsRef.current) {
                featureDetailsRef.current.classList.add('active');
            }
        }, 10);
    };

    // Handler for closing feature details
    const handleCloseDetails = () => {
        if (featureDetailsRef.current) {
            featureDetailsRef.current.classList.remove('active');
            
            // Wait for animation to complete before removing modal
            setTimeout(() => {
                setShowFeatureDetails(null);
            }, 400);
        } else {
            setShowFeatureDetails(null);
        }
    };

    // Validate feature selections
    const validateSelections = () => {
        // Check if all required choices are made
        const missingChoices = Object.entries(selectedChoices)
            .filter(([featureId, choiceId]) => choiceId === null)
            .map(([featureId]) => featureId);
        
        if (missingChoices.length > 0) {
            return {
                valid: false,
                message: `Please make selections for: ${missingChoices.join(', ')}`
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
        
        // Update character data with selected features
        updateCharacterData({
            classFeatures: {
                required: requiredFeatures.map(f => f.id),
                optional: selectedChoices
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
                <div>Loading Class Features...</div>
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
        <div className="step6-outer-container">
            {/* Title */}
            <h2 className="step6-title">{characterData.className} Features</h2>
            
            {/* Required Features Section */}
            {requiredFeatures.length > 0 && (
                <div className="features-section">
                    <h3 className="section-heading">Class Features</h3>
                    <p className="section-description">
                        At 1st level, your {characterData.className} gains the following features:
                    </p>
                    
                    <div className="feature-grid">
                        {requiredFeatures.map((feature, index) => (
                            <div key={index} className="feature-card required-feature">
                                <div className="feature-header">
                                    <h4 className="feature-name">{feature.name}</h4>
                                    <div className={`feature-type-badge ${feature.type === 'active' ? 'active-type' : 'passive-type'}`}>
                                        {feature.type === 'active' ? 'Active' : 'Passive'}
                                    </div>
                                </div>
                                
                                <p className="feature-description">
                                    {feature.description.length > 150 ? 
                                        `${feature.description.substring(0, 150)}...` : 
                                        feature.description}
                                </p>
                                
                                {feature.description.length > 150 && (
                                    <button 
                                        className="details-button"
                                        onClick={() => handleShowDetails(feature)}
                                    >
                                        See Details
                                    </button>
                                )}
                                
                                {feature.usageLimit && (
                                    <div className="feature-usage">
                                        <i className="bi bi-clock"></i> {feature.usageLimit}
                                    </div>
                                )}
                                
                                {feature.actionType && (
                                    <div className="feature-action-type">
                                        <i className="bi bi-lightning"></i> {feature.actionType}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}
            
            {/* Optional Features Section */}
            {optionalFeatures.length > 0 && (
                <div className="features-section">
                    <h3 className="section-heading">Choose Your Features</h3>
                    <p className="section-description">
                        Select options for your class features:
                    </p>
                    
                    {optionalFeatures.map((featureGroup, groupIndex) => (
                        <div key={groupIndex} className="feature-group">
                            <h4 className="feature-group-name">{featureGroup.name}</h4>
                            <p className="feature-group-description">{featureGroup.description}</p>
                            
                            {featureGroup.type === 'choice' && featureGroup.choices && (
                                <div className={`choice-grid ${!selectedChoices[featureGroup.id] ? 'needs-selection' : ''}`}>
                                    {featureGroup.choices.map((choice, choiceIndex) => (
                                        <div 
                                            key={choiceIndex} 
                                            className={`choice-card ${selectedChoices[featureGroup.id] === choice.id ? 'selected' : ''}`}
                                            onClick={() => handleChoiceSelect(featureGroup.id, choice.id)}
                                        >
                                            <div className="choice-header">
                                                <h5 className="choice-name">{choice.name}</h5>
                                            </div>
                                            
                                            <p className="choice-description">
                                                {choice.description.length > 120 ? 
                                                    `${choice.description.substring(0, 120)}...` : 
                                                    choice.description}
                                            </p>
                                            
                                            {choice.description.length > 120 && (
                                                <button 
                                                    className="details-button"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        handleShowDetails(choice);
                                                    }}
                                                >
                                                    See Details
                                                </button>
                                            )}
                                            
                                            {choice.benefit && (
                                                <div className="choice-benefit">
                                                    <i className="bi bi-star-fill"></i> {choice.benefit}
                                                </div>
                                            )}
                                            
                                            <div className="selected-indicator">
                                                <i className="bi bi-check-circle-fill"></i> Selected
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
            
            {/* Feature Details Modal */}
            {showFeatureDetails && (
                <div 
                    className="feature-details-overlay" 
                    ref={featureDetailsRef} 
                    onClick={handleCloseDetails}
                >
                    <div className="feature-details-modal" onClick={(e) => e.stopPropagation()}>
                        <button className="close-button" onClick={handleCloseDetails}>×</button>
                        
                        <div className="feature-details-header">
                            <h3 className="feature-details-name">{showFeatureDetails.name}</h3>
                            {showFeatureDetails.type && (
                                <div className={`feature-details-type ${showFeatureDetails.type === 'active' ? 'active-type' : 'passive-type'}`}>
                                    {showFeatureDetails.type === 'active' ? 'Active' : 'Passive'}
                                </div>
                            )}
                        </div>
                        
                        <div className="feature-details-content">
                            <p className="feature-details-description">{showFeatureDetails.description}</p>
                            
                            {showFeatureDetails.usageLimit && (
                                <div className="feature-details-usage">
                                    <h4>Usage</h4>
                                    <p>{showFeatureDetails.usageLimit}</p>
                                </div>
                            )}
                            
                            {showFeatureDetails.actionType && (
                                <div className="feature-details-action">
                                    <h4>Action</h4>
                                    <p>{showFeatureDetails.actionType}</p>
                                </div>
                            )}
                            
                            {showFeatureDetails.benefit && (
                                <div className="feature-details-benefit">
                                    <h4>Benefit</h4>
                                    <p>{showFeatureDetails.benefit}</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
            
            {/* Navigation Buttons */}
            <div className="step6-navigation">
                <button className="back-button" onClick={prevStep}>
                    <i className="bi bi-arrow-left"></i> Back to Abilities
                </button>
                
                <button 
                    className={`continue-button ${validateSelections().valid ? 'active' : ''}`}
                    onClick={handleContinue}
                    disabled={!validateSelections().valid}
                >
                    Continue to Spells <i className="bi bi-arrow-right"></i>
                </button>
            </div>
        </div>
    );
}

export default Step6_ClassFeatures;