import React, { useState, useEffect, useCallback } from 'react';
import './CharacterCreator.css';

// Import step components
import Step1_WorldSelector from './steps/Step1_WorldSelector';
import Step2_CampaignSelector from './steps/Step2_CampaignSelector';
import Step3_ClassSelector from './steps/Step3_ClassSelector';
import Step4_CharacterInfo from './steps/Step4_CharacterInfo';
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
            case 3:
                return (
                    <Step3_ClassSelector
                        characterData={characterData}
                        updateCharacterData={updateCharacterData}
                        nextStep={nextStep}
                        prevStep={prevStep}
                    />
                )
            case 4:
                return (
                    <Step4_CharacterInfo
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

    const useCardWrapper = ![1,2].includes(currentStep);

    // Main component return
    return (
        <div className="character-creator-container">
            {currentStep > 1 && (
                <header className='text-center mb-4'>
                </header>
            )}
    
            {/* Loading and error display */}
            {isLoading && <div className="text-center text-light">Loading...</div>}
            {error && <div className="alert alert-danger" role="alert">{error}</div>}
    
            {!isLoading && !error && (
                useCardWrapper ? (
                    // Steps 3+ get the card wrapper (for forms, etc.)
                    <div className="row justify-content-center">
                        <div className={`${currentStep === 3 ? 'col-md-12' : 'col-md-10 col-lg-8'}`}>
                            <div className="card character-card">
                                <div className="card-body">
                                    {renderCurrentStep()}
                                </div>
                            </div>
                        </div>
                    </div>
                ) : (
                    // Steps 1 and 2 render without the card wrapper
                    renderCurrentStep()
                )
            )}
        </div>
    );
}



export default CharacterCreator;