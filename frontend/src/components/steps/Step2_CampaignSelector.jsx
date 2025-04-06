// File: frontend/src/components/steps/Step2_CampaignSelector.jsx

import React, { useState, useEffect, useCallback } from 'react';
import './Step2_CampaignSelector.css'; // We'll create new styles

function Step2_CampaignSelector({ characterData, updateCharacterData, nextStep, prevStep }) {
    const [campaigns, setCampaigns] = useState([]);
    // State to hold the *full data* of the selected campaign for the details panel
    const [selectedCampaignDetails, setSelectedCampaignDetails] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);

    // Fetch campaigns
    useEffect(() => {
        if (!characterData.worldId) {
            setError("No world selected. Please go back to Step 1.");
            setIsLoading(false);
            return;
        }

        setIsLoading(true);
        setError(null);
        console.log(`Step2: Fetching campaigns for world: ${characterData.worldId}...`);

        fetch(`/characters/api/campaigns/${characterData.worldId}`)
            .then(response => {
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                return response.json();
            })
            .then(data => {
                console.log("Step2: Campaigns fetched:", data);
                if (data.success && Array.isArray(data.campaigns)) {
                    // Ensure "DM Creates" is last
                    const dmOption = data.campaigns.find(c => c.is_default);
                    const otherCampaigns = data.campaigns.filter(c => !c.is_default);
                    const sortedCampaigns = dmOption ? [...otherCampaigns, dmOption] : otherCampaigns;

                    setCampaigns(sortedCampaigns);

                    // Pre-select based on existing character data or default to DM option if available
                    const currentCampaignId = characterData.campaignId;
                    let initialSelection = null;
                    if (currentCampaignId) {
                         initialSelection = sortedCampaigns.find(c => c.id === currentCampaignId);
                    }
                    // If no current selection or not found, try selecting the default DM option
                    if (!initialSelection && dmOption) {
                         initialSelection = dmOption;
                    }
                     // If still nothing selected, maybe select the first one? Or leave null?
                     // Selecting the DM option is a safe default.
                     setSelectedCampaignDetails(initialSelection);

                } else {
                    throw new Error(data.error || 'Invalid data format for campaigns.');
                }
                setIsLoading(false);
            })
            .catch(err => {
                console.error("Step2: Failed to fetch campaigns:", err);
                setError(`Failed to load campaigns: ${err.message}. Check API endpoint or server logs.`);
                setIsLoading(false);
            });
    }, [characterData.worldId, characterData.campaignId]); // Refetch if world changes, update selection if campaignId changes

    // Handler when a campaign is clicked in the list
    const handleCampaignSelect = useCallback((campaign) => {
        setSelectedCampaignDetails(campaign);
    }, []);

    // Handler for the final confirmation button
    const handleConfirmCampaign = () => {
        if (!selectedCampaignDetails) {
             setError("Please select a campaign option.");
             return;
        }

        console.log(`Campaign confirmed: ${selectedCampaignDetails.name}`);
        updateCharacterData({
            campaignId: selectedCampaignDetails.id,
            campaignName: selectedCampaignDetails.name,
            // Reset subsequent steps
            classId: null,
            // ... reset other relevant fields ...
        });
        nextStep(); // Proceed to Step 3 (Class Choice)
    };

    // --- Render Logic ---
    if (isLoading) {
        return <div className="loading-container"><div className="spinner-border" role="status"></div> Loading Campaigns...</div>;
    }

    if (error) {
        // Added a button to go back if there's an error
        return (
             <div className="error-container alert alert-danger">
                <p>{error}</p>
                 <button className="btn btn-secondary btn-sm" onClick={prevStep}>
                    Go Back
                </button>
            </div>
        );
    }

    return (
        <div className="step2-container">
            {/* Left Column: Campaign List */}
            <div className="campaign-list-column">
                <h4 className="list-header">Select a Campaign</h4>
                <div className="campaign-list-scrollable">
                    {campaigns.map((campaign) => (
                        <div
                            key={campaign.id}
                            className={`campaign-list-item ${selectedCampaignDetails?.id === campaign.id ? 'selected' : ''} ${campaign.is_default ? 'default-option' : ''}`}
                            onClick={() => handleCampaignSelect(campaign)}
                            style={{ backgroundImage: campaign.image ? `url(${campaign.image})` : 'none' }}
                        >
                            <div className="item-overlay">
                                <span className="item-title">{campaign.name}</span>
                            </div>
                             {/* Selection Indicator (optional visual cue) */}
                             {selectedCampaignDetails?.id === campaign.id && (
                                 <div className="list-item-selected-indicator">
                                     <i className="bi bi-check-lg"></i>
                                 </div>
                             )}
                        </div>
                    ))}
                </div>
            </div>

            {/* Right Column: Campaign Details */}
            <div className="campaign-details-column">
                {selectedCampaignDetails ? (
                    <div className="campaign-details-panel">
                        {/* Use a container for the image to control its size/aspect ratio */}
                        {selectedCampaignDetails.image && (
                             <div className="details-image-container">
                                 <img src={selectedCampaignDetails.image} alt={selectedCampaignDetails.name} className="details-image"/>
                             </div>
                         )}
                        <div className="details-content">
                            <h3>{selectedCampaignDetails.name}</h3>
                            <p className="details-description">{selectedCampaignDetails.description}</p>
                            <div className="details-info">
                                {selectedCampaignDetails.themes && <div><strong>Themes:</strong> {selectedCampaignDetails.themes.join(', ')}</div>}
                                {selectedCampaignDetails.estimated_length && <div><strong>Length:</strong> {selectedCampaignDetails.estimated_length}</div>}
                                {selectedCampaignDetails.leveling && <div><strong>Leveling:</strong> {selectedCampaignDetails.leveling}</div>}
                            </div>
                             <button
                                className="btn btn-primary btn-lg mt-4 confirm-button"
                                onClick={handleConfirmCampaign}
                             >
                                Confirm Campaign <i className="bi bi-check-lg ms-2"></i>
                             </button>
                        </div>
                    </div>
                ) : (
                    // Placeholder if nothing is selected (optional)
                    <div className="details-placeholder">
                        <p>Select a campaign from the list to see details.</p>
                    </div>
                )}
            </div>

             {/* Navigation Buttons (Bottom of the whole step) */}
            <div className="step2-navigation">
                <button className="btn btn-secondary" onClick={prevStep}>
                    <i className="bi bi-arrow-left me-2"></i>Back to World Choice
                </button>
                {/* Confirmation is now inside the details panel */}
            </div>
        </div>
    );
}

export default Step2_CampaignSelector;