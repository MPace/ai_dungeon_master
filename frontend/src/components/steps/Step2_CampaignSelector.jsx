// File: frontend/src/components/steps/Step2_CampaignSelector.jsx

import React, { useState, useEffect, useCallback } from 'react';
import './Step2_CampaignSelector.css'; // Styles will be updated

function Step2_CampaignSelector({ characterData, updateCharacterData, nextStep, prevStep }) {
    const [campaigns, setCampaigns] = useState([]);
    // State to hold the *full data* of the campaign selected for the details overlay
    const [selectedCampaignDetails, setSelectedCampaignDetails] = useState(null); // Initialize as null
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
        fetch(`/characters/api/campaigns/${characterData.worldId}`)
            .then(response => {
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                return response.json();
            })
            .then(data => {
                if (data.success && Array.isArray(data.campaigns)) {
                    // Filter out any null or undefined items just to be safe
                    const validCampaigns = data.campaigns.filter(c => c);
                    const dmOption = validCampaigns.find(c => c.is_default);
                    const otherCampaigns = validCampaigns.filter(c => !c.is_default);
                    const sortedCampaigns = dmOption ? [...otherCampaigns, dmOption] : otherCampaigns;
                    setCampaigns(sortedCampaigns);
                    // DO NOT set selectedCampaignDetails here initially
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
    }, [characterData.worldId]); // Only fetch when worldId changes

    // Helper to get the full image URL
    const getFullImageUrl = (imagePath) => {
        if (!imagePath) {
            return null;
        }
        
        // If it's already a full URL (http or https), use it directly
        if (imagePath.startsWith('http://') || imagePath.startsWith('https://')) {
            return imagePath;
        }
        
        // Match the exact pattern that works for world images
        // Note the /build/ part that's missing in the failing URL
        return `/static/build/${imagePath.startsWith('/') ? imagePath.substring(1) : imagePath}`;
    }

    // Handler when a campaign LIST ITEM is clicked
    const handleCampaignSelect = useCallback((campaign) => {
        console.log("Campaign selected for details view:", campaign.name);
        setSelectedCampaignDetails(campaign); // Set details to show the overlay
    }, []);

    // Handler to close the details overlay
    const closeDetailsPanel = useCallback(() => {
        setSelectedCampaignDetails(null);
    }, []);

    // Handler for the final confirmation button (inside the details overlay)
    const handleConfirmCampaign = () => {
        if (!selectedCampaignDetails) return; // Should not happen if button is only in details

        console.log(`Campaign confirmed: ${selectedCampaignDetails.name}`);
        updateCharacterData({
            campaignId: selectedCampaignDetails.id,
            campaignName: selectedCampaignDetails.name,
            classId: null, // Reset subsequent steps
        });
        nextStep();
    };

    // --- Render Logic ---
    if (isLoading) {
        return <div className="loading-container"><div className="spinner-border" role="status"></div> Loading Campaigns...</div>;
    }

    if (error) {
        return (
            <div className="error-container alert alert-danger">
                <p>{error}</p>
                <button className="btn btn-secondary btn-sm" onClick={prevStep}>Go Back</button>
            </div>
        );
    }

    // Main component structure: Title, List, Overlay (conditional), Navigation
    return (
        <div className="step2-outer-container"> {/* Use a simple outer container */}
            {/* Title styled like Step 1 */}
            <h2 className="step2-title">Choose Your Campaign</h2>

            {/* Vertically scrollable list */}
            <div className="campaign-list-scrollable-outer">
                <div className="campaign-list">
                    {campaigns.map((campaign) => {
                        // Defensive check to ensure campaign is valid
                        if (!campaign) {
                            console.warn("Received null or undefined campaign in data");
                            return null; // Skip this item
                        }

                        // Safely access image property
                        const backgroundImageUrl = campaign.image ? getFullImageUrl(campaign.image) : null;
                        
                        // Log for debugging
                        console.log(`Campaign: ${campaign.name}, Image: ${campaign.image}, URL: ${backgroundImageUrl}`);
                        
                        const itemStyle = backgroundImageUrl
                            ? { backgroundImage: `linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.7)), url(${backgroundImageUrl})` }
                            : { backgroundImage: 'linear-gradient(#333, #222)' }; // Fallback gradient

                        return (
                            <div
                                key={campaign.id}
                                className={`campaign-list-item ${selectedCampaignDetails?.id === campaign.id ? 'selected' : ''} ${campaign.is_default ? 'default-option' : ''}`}
                                onClick={() => handleCampaignSelect(campaign)}
                                style={itemStyle} // Use the generated style object
                            >
                                <div className="item-overlay"> {/* Keep overlay for text */}
                                    <span className="item-title">{campaign.name || "Unnamed Campaign"}</span>
                                </div>
                                {/* Selection Indicator */}
                                {selectedCampaignDetails?.id === campaign.id && (
                                    <div className="list-item-selected-indicator">
                                        <i className="bi bi-check-lg"></i>
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Details Panel Overlay - Conditionally Rendered */}
            {selectedCampaignDetails && (
                <div className="details-backdrop" onClick={closeDetailsPanel}> {/* Backdrop closes panel */}
                    <div className="campaign-details-panel" onClick={(e) => e.stopPropagation()}> {/* Prevent clicks inside from closing */}
                        <button className="close-details-btn" onClick={closeDetailsPanel}>×</button>
                        {selectedCampaignDetails.image && (
                            <div className="details-image-container">
                                <img 
                                    src={getFullImageUrl(selectedCampaignDetails.image)} 
                                    alt={selectedCampaignDetails.name} 
                                    className="details-image"
                                />
                            </div>
                        )}
                        <div className="details-content">
                            <h3>{selectedCampaignDetails.name || "Campaign Details"}</h3>
                            <p className="details-description">{selectedCampaignDetails.description || "No description available"}</p>
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
                </div>
            )}

            {/* Navigation Buttons (Bottom) */}
            <div className="step2-navigation">
                <button className="btn btn-secondary" onClick={prevStep}>
                    <i className="bi bi-arrow-left me-2"></i>Back to World Choice
                </button>
                {/* Continue button removed, confirmation happens in details panel */}
            </div>
        </div>
    );
}

export default Step2_CampaignSelector;