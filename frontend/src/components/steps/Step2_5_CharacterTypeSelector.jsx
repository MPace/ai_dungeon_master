// File: frontend/src/components/steps/Step2_5_CharacterTypeSelector.jsx

import React from 'react';
import './Step2_5_CharacterTypeSelector.css';

function Step2_5_CharacterTypeSelector({ characterData, updateCharacterData, nextStep, prevStep }) {
    // Character type options
    const characterTypes = [
        {
            id: 'premade',
            name: 'Premade Character',
            description: 'Choose from a selection of ready-to-play characters perfect for new players. Get started quickly without worrying about character creation details.',
            image: '/images/icons/premade_characters.jpg'
        },
        {
            id: 'custom',
            name: 'Custom Character',
            description: 'Create your own unique character from scratch. Choose your race, class, abilities, and more for a fully personalized adventure.',
            image: '/images/icons/custom_character.jpg'
        }
    ];

    // Handle selection of character type
    const handleSelectType = (typeId) => {
        updateCharacterData({
            characterType: typeId
        });
        
        if (typeId === 'premade') {
            // Go to premade character selection
            nextStep(true);
        } else {
            // Go to regular character creation flow
            nextStep(false);
        }
    };

    return (
        <div className="character-type-selector-container">
            <h2 className="character-type-title">Choose Your Path</h2>
            <p className="character-type-description">
                Would you like to use a premade character or create your own?
            </p>
            
            <div className="character-type-options">
                {characterTypes.map((type) => (
                    <div 
                        key={type.id} 
                        className="character-type-card"
                        onClick={() => handleSelectType(type.id)}
                    >
                        <div className="character-type-image-container">
                            <img 
                                src={type.image} 
                                alt={type.name} 
                                className="character-type-image"
                                onError={(e) => {
                                    e.target.src = '/images/icons/default_character_type.jpg'; 
                                    e.target.onerror = null;
                                }}
                            />
                        </div>
                        <div className="character-type-content">
                            <h3 className="character-type-name">{type.name}</h3>
                            <p className="character-type-desc">{type.description}</p>
                        </div>
                        <div className="character-type-select-btn">
                            Select
                        </div>
                    </div>
                ))}
            </div>
            
            {/* Navigation Buttons */}
            <div className="character-type-navigation">
                <button className="back-button" onClick={prevStep}>
                    <i className="bi bi-arrow-left"></i> Back to Campaign
                </button>
            </div>
        </div>
    );
}

export default Step2_5_CharacterTypeSelector;