import React, { useState, useEffect, useCallback } from 'react';

// Import step components
import Step1_WorldSelector from './steps/Step1_WorldSelector';
// import Step2_CampaignSelector from './steps/Step2_CampaignSelector';
// ... import other step components as they are created

// --- Initial Character Data Structure ---
const initialCharacterData = {
    // Step 1
    worldId: null,
    worldName: null,
    // Step 2
    campaignId: null,
    campaignName: null,
    campaignMode: 'pre-made',
    // Step 3
    classId: null,
    className: null,
    // Step 4
    name: '',
    raceId: null,
    raceName: null,
    subRaceId: null,
    subRaceName: null,
    backgroundId: null,
    backgroundName: null,
    // Step 5 (Abilities)
    abilities: {
        strength: 8,
        dexterity: 8,
        constitution: 8,
        intelligence: 8,
        wisdom: 8,
        charisma: 8
    },
    // Step 6 (Proficiencies)
    proficiencies: {
        skills: [],
        tools: [],
        languages: [],
        armor: [],
        weapons: []
    },
    // Step 7 (Features)
    features: {},
    // Step 8 (Spells)
    spellcasting: {},
    // Step 9 (Equipment)
    equipment: {},
    // Step 10 (Finalization)
    description: '',
    // Meta
    isDraft: true,
    characterId: null,
    lastStepCompleted: 0,
};

function CharacterCreator() {
    const [currentStep, setCurrentStep] = useState(1);
    const [characterData, setCharacterData] = useState(initialCharacterData);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);

    // --- Navigation Functions ---
    const nextStep = useCallback(() => {
        setCurrentStep(prevStep => {
            const next = prevStep + 1;
            // Update last step completed *before* moving
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

    // --- Data Update Function ---
    const updateCharacterData = useCallback((newData) => {
        setCharacterData(prevData => ({
            ...prevData,
            ...newData,
        }));
        console.log("Character data updated:", newData);
    }, []);

    // --- Component Rendering Logic ---
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
            // Add cases for other steps as components are created
            default:
                return <div>Step {currentStep} - Component not implemented yet.</div>;
        }
    };

    // --- Render Step Indicator (Optional but helpful) ---
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
                    // Make indicator clickable to navigate back
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

    // --- Main Component Return ---
    return (
        <div className="container-fluid character-creator-container">
            <header className="text-center mb-4">
                <h1 className="display-4 text-light">Character Creation</h1>
            </header>

            {/* Optional: Loading and Error Display */}
            {isLoading && <div className="text-center text-light">Loading...</div>}
            {error && <div className="alert alert-danger" role="alert">{error}</div>}
            
            {/* For step 1, we want a full-width display without the step indicator */}
            {currentStep === 1 ? (
                <div className="row">
                    <div className="col-12">
                        {renderCurrentStep()}
                    </div>
                </div>
            ) : (
                <div className="row justify-content-center">
                    <div className="col-md-10 col-lg-8">
                        {/* Step indicator for steps 2+ */}
                        {renderStepIndicator()}
                        
                        <div className="card character-card">
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