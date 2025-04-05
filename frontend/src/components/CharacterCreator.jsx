import React, { useState, useEffect, useCallback } from 'react';

// Import step components (we'll create Step1 first, others later)
import Step1_WorldSelector from './steps/Step1_WorldSelector';
// import Step2_CampaignSelector from './steps/Step2_CampaignSelector';
// import Step3_ClassSelector from './steps/Step3_ClassSelector';
// ... import other step components as they are created

// --- Initial Character Data Structure ---
// Define the basic structure of the character object
const initialCharacterData = {
    // Step 1
    worldId: null,
    worldName: null, // Optional: Store name for display
    // Step 2
    campaignId: null,
    campaignName: null, // Optional
    campaignMode: 'pre-made', // 'pre-made' or 'ai-generated'
    // Step 3
    classId: null,
    className: null, // Optional
    // Step 4
    name: '',
    raceId: null,
    raceName: null, // Optional
    subRaceId: null,
    subRaceName: null, // Optional
    backgroundId: null,
    backgroundName: null, // Optional
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
    features: {
        // e.g., fighting_style: 'defense', cleric_domain: 'life'
    },
    // Step 8 (Spells)
    spellcasting: {
        // cantripsKnown: [], spellsKnown: [], spellsPrepared: [] etc.
    },
    // Step 9 (Equipment)
    equipment: {
        // selectedPackageId: null, startingGold: 0, items: []
    },
    // Step 10 (Finalization)
    description: '',
    // --- Meta ---
    isDraft: true, // Mark as draft initially
    characterId: null, // Will be assigned upon first save/draft
    lastStepCompleted: 0, // Track progress
};

function CharacterCreator() {
    const [currentStep, setCurrentStep] = useState(1);
    const [characterData, setCharacterData] = useState(initialCharacterData);
    // Add loading/error states if needed for API calls
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
        // Optional: Add logic to prevent jumping ahead if steps aren't complete
        if (step <= characterData.lastStepCompleted + 1 && step >= 1) {
             setCurrentStep(step);
        } else {
            console.warn(`Cannot jump to step ${step} from step ${currentStep} (last completed: ${characterData.lastStepCompleted})`);
        }
    }, [characterData.lastStepCompleted, currentStep]);


    // --- Data Update Function ---
    // Merges new data into the existing characterData state
    const updateCharacterData = useCallback((newData) => {
        setCharacterData(prevData => ({
            ...prevData,
            ...newData,
            // Automatically update nested objects if needed, e.g., abilities
            // You might need more sophisticated merging logic for nested state
        }));
        // Optional: Trigger autosave here or manage via useEffect
        console.log("Character data updated:", characterData);
    }, [characterData]); // Include characterData dependency if logic inside depends on it

    // --- Component Rendering Logic ---
    const renderCurrentStep = () => {
        switch (currentStep) {
            case 1:
                return (
                    <Step1_WorldSelector
                        characterData={characterData}
                        updateCharacterData={updateCharacterData}
                        nextStep={nextStep}
                        // No prevStep on step 1
                    />
                );
            // --- Add cases for other steps as components are created ---
            // case 2:
            //     return (
            //         <Step2_CampaignSelector
            //             characterData={characterData}
            //             updateCharacterData={updateCharacterData}
            //             nextStep={nextStep}
            //             prevStep={prevStep}
            //         />
            //     );
            // case 3:
            //     return (
            //         <Step3_ClassSelector ... />
            //     );
            // ... and so on for steps 4 through 10

            default:
                return <div>Step {currentStep} - Component not implemented yet.</div>;
        }
    };

    // --- Render Step Indicator (Optional but helpful) ---
    const renderStepIndicator = () => {
        const totalSteps = 10; // Adjust if number of steps changes
        return (
            <div className="step-indicator mb-4" style={{ display: 'flex', justifyContent: 'center' }}>
                {[...Array(totalSteps)].map((_, index) => {
                    const stepNumber = index + 1;
                    let stepClass = 'step'; // Use your existing CSS class
                    if (stepNumber === currentStep) {
                        stepClass += ' active';
                    } else if (stepNumber <= characterData.lastStepCompleted) {
                        stepClass += ' completed';
                    }
                    // Make indicator clickable to navigate back
                    return (
                         <div key={stepNumber} className={stepClass} onClick={() => goToStep(stepNumber)} style={{cursor: 'pointer'}}>
                             {stepNumber}
                         </div>
                    );
                })}
            </div>
        );
     };


    // --- Main Component Return ---
    return (
        // Use a container structure similar to your create.html
        <div className="container-fluid px-4 py-3">
             <header className="text-center mb-4">
                <h1 className="display-4 text-light">Character Creation</h1>
            </header>

            {/* Optional: Loading and Error Display */}
            {isLoading && <div className="text-center text-light">Loading...</div>}
            {error && <div className="alert alert-danger" role="alert">{error}</div>}

            <div className="row justify-content-center">
                <div className="col-md-10 col-lg-8">
                    
                    <div className="card character-card">
                        <div className="card-body">
                           {/* Render the component for the current step */}
                           {renderCurrentStep()}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default CharacterCreator;