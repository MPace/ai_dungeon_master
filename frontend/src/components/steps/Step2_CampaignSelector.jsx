// File: frontend/src/components/steps/Step2_CampaignSelector.jsx

import React, { useState, useEffect } from 'react';
import './Step2_CampaignSelector.css'; // We'll create this CSS file next

function Step2_CampaignSelector({ characterData, updateCharacterData, nextStep, prevStep }) {
    const [campaigns, setCampaigns] = useState([]);
    const [selectedCampaignId, setSelectedCampaignId] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);

    // Fetch campaigns when the component mounts or worldId changes
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
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log("Step2: Campaigns fetched:", data);
                if (data.success && Array.isArray(data.campaigns)) {
                    setCampaigns(data.campaigns);
                    // Pre-select the DM created option if nothing else is selected
                    if (!selectedCampaignId && data.campaigns.length > 0) {
                         const defaultCampaign = data.campaigns.find(c => c.is_default);
                         if (defaultCampaign && !characterData.campaignId) {
                             setSelectedCampaignId(defaultCampaign.id);
                         } else if (characterData.campaignId) {
                            setSelectedCampaignId(characterData.campaignId);
                         }
                    }
                } else {
                    throw new Error(data.error || 'Invalid data format for campaigns.');
                }
                setIsLoading(false);
            })
            .catch(err => {
                console.error("Step2: Failed to fetch campaigns:", err);
                setError(`Failed to load campaigns: ${err.message}. Check API endpoint.`);
                setIsLoading(false);
            });
    }, [characterData.worldId]); // Re-fetch if worldId changes

    const handleCampaignSelect = (campaignId) => {
        setSelectedCampaignId(campaignId);
    };

    const handleConfirmCampaign = () => {
        if (!selectedCampaignId) {
             setError("Please select a campaign option.");
             return;
         }
        const selectedCampaign = campaigns.find(c => c.id === selectedCampaignId);
        if (!selectedCampaign) {
             setError("Selected campaign not found.");
             return;
         }

        console.log(`Campaign confirmed: ${selectedCampaign.name}`);
        updateCharacterData({
            campaignId: selectedCampaign.id,
            campaignName: selectedCampaign.name,
            // Reset subsequent steps if campaign changes
            classId: null,
            race: null,
            // etc.
        });
        nextStep(); // Proceed to Step 3 (Class Choice)
    };

    // --- Render Logic ---
    if (isLoading) {
        return <div className="text-center p-5"><div className="spinner-border spinner-border-sm" role="status"></div> Loading Campaigns...</div>;
    }

    if (error) {
        return <div className="alert alert-danger">{error}</div>;
    }

    return (
        <div className="campaign-selector-container">
            <h3 className="mb-4 text-light text-center">Choose Your Campaign for {characterData.worldName || 'the World'}</h3>
            <div className="campaign-grid">
                {campaigns.map((campaign) => (
                    <div
                        key={campaign.id}
                        className={`campaign-card selection-card ${selectedCampaignId === campaign.id ? 'selected' : ''} ${campaign.is_default ? 'default-option' : ''}`}
                        onClick={() => handleCampaignSelect(campaign.id)}
                    >
                        <div className="card-body">
                            {campaign.image && (
                                <img src={campaign.image} alt={campaign.name} className="campaign-image mb-2"/>
                            )}
                            <h5 className="card-title">{campaign.name}</h5>
                            <p className="card-text small campaign-description">{campaign.description}</p>
                            <div className="campaign-details small">
                                {campaign.themes && <div><strong>Themes:</strong> {campaign.themes.join(', ')}</div>}
                                {campaign.estimated_length && <div><strong>Length:</strong> {campaign.estimated_length}</div>}
                                {campaign.leveling && <div><strong>Leveling:</strong> {campaign.leveling}</div>}
                            </div>
                        </div>
                        <div className="card-footer">
                            <div className="selected-indicator">
                                <i className="bi bi-check-circle-fill"></i> Selected
                            </div>
                        </div>
                    </div>
                ))}
            </div>
            <div className="navigation-buttons mt-4 d-flex justify-content-between">
                <button className="btn btn-secondary" onClick={prevStep}>
                    <i className="bi bi-arrow-left me-2"></i>Back to World Choice
                </button>
                <button
                    className="btn btn-primary"
                    onClick={handleConfirmCampaign}
                    disabled={!selectedCampaignId}
                 >
                    Continue to Class Choice<i className="bi bi-arrow-right ms-2"></i>
                </button>
            </div>
        </div>
    );
}

export default Step2_CampaignSelector;