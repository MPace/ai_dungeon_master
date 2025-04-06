import React, { useState, useEffect, useCallback } from 'react';
import './CharacterCreator.css';

// Import step components
import Step1_WorldSelector from './steps/Step1_WorldSelector';
import Step2_CampaignSelector from './steps/Step2_CampaignSelector';
// Import other steps when ready

const initialCharacterData = {
    // Data structure as before
    worldId: null,
    worldName: null,
    // Rest of the structure
    isDraft: true,
    characterId: null,
    lastStepCompleted: 0,
};

function CharacterCreator() {
    const [currentStep, setCurrentStep] = useState(1);
    const [characterData, setCharacterData] = useState(initialCharacterData);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);

    // Navigation functions
    const nextStep = useCallback(() => {
        setCurrentStep(prevStep => {
            const next = prevStep + 1;
            setCharacterData(prevData => ({
                ...prevData,
                lastStepCompleted: Math.max(prevData.lastStepCompleted, prevStep)
            }));
            return next;
        });
    }, []);

    const prevStep = useCallback(() => {
        setCurrentStep(prevStep => Math.max(1, prevStep - 1));
    }, []);

    const goToStep = useCallback((step) => {
        if (step <= characterData.lastStepCompleted + 1 && step >= 1) {
             setCurrentStep(step);
        } else {
            console.warn(`Cannot jump to step ${step} from step ${currentStep} (last completed: ${characterData.lastStepCompleted})`);
        }
    }, [characterData.lastStepCompleted, currentStep]);

    // Data update function
    const updateCharacterData = useCallback((newData) => {
        setCharacterData(prevData => ({
            ...prevData,
            ...newData,
        }));
        console.log("Character data updated:", newData);
    }, []);

    // Render logic
    const renderCurrentStep = () => {
        switch (currentStep) {
            case 1:
                return (
                    <Step1_WorldSelector
                        characterData={characterData}
                        updateCharacterData={updateCharacterData}
                        nextStep={nextStep}
                    />
                );
            case 2:
                return (
                    <Step2_CampaignSelector
                        characterData={characterData}
                        updateCharacterData={updateCharacterData}
                        nextStep={nextStep}
                        prevStep={prevStep}
                    />
                )
            // Add cases for other steps
            default:
                return <div>Step {currentStep} - Component not implemented yet.</div>;
        }
    };

    // Step indicator
    const renderStepIndicator = () => {
        const totalSteps = 10;
        return (
            <div className="step-indicator mb-4">
                {[...Array(totalSteps)].map((_, index) => {
                    const stepNumber = index + 1;
                    let stepClass = 'step';
                    if (stepNumber === currentStep) {
                        stepClass += ' active';
                    } else if (stepNumber <= characterData.lastStepCompleted) {
                        stepClass += ' completed';
                    }
                    return (
                         <div 
                             key={stepNumber} 
                             className={stepClass} 
                             onClick={() => goToStep(stepNumber)} 
                             style={{cursor: 'pointer'}}
                         >
                             {stepNumber}
                         </div>
                    );
                })}
            </div>
        );
    };

    // Main component return
    return (
        // Consider a conditional class: className={`character-creator-container ${currentStep === 1 ? 'step1-layout' : 'standard-layout'}`}
        <div className="character-creator-container">
            {/* We only need the main header for steps 2+ */}
            {currentStep > 1 && (
                <header className="text-center mb-4">
                    {/* You might want a more specific header per step later */}
                    <h1 className="display-4 text-light">Character Creation - Step {currentStep}</h1>
                </header>
            )}

            {/* Loading and error display */}
            {isLoading && <div className="text-center text-light">Loading...</div>}
            {error && <div className="alert alert-danger" role="alert">{error}</div>}

            {/* For step 1, we use a distinct layout (like the full-page world selector) */}
            {currentStep === 1 ? (
                 // Step 1 component doesn't need the card wrapper or step indicator
                 renderCurrentStep()
            ) : (
                 // For steps 2+, wrap content in a standard centered layout
                <div className="row justify-content-center">
                    <div className="col-md-10 col-lg-8">
                        {/* REMOVED: renderStepIndicator() was here */}

                        <div className="card character-card"> {/* Re-use styling */}
                            <div className="card-body">
                                {renderCurrentStep()}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default CharacterCreator;