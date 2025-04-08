// File: frontend/src/components/steps/Step2_CampaignSelector.jsx

import React, { useState, useEffect, useCallback, useRef } from 'react';
import './Step2_CampaignSelector.css';

function Step2_CampaignSelector({ characterData, updateCharacterData, nextStep, prevStep }) {
    const [campaigns, setCampaigns] = useState([]);
    const [selectedCampaignDetails, setSelectedCampaignDetails] = useState(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    
    // Ref for modal
    const modalRef = useRef(null);

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
    }, [characterData.worldId]);

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
        return `/static/build/${imagePath.startsWith('/') ? imagePath.substring(1) : imagePath}`;
    }

    // Handler when a campaign card is clicked
    const handleCampaignSelect = useCallback((campaign) => {
        console.log("Campaign selected for details view:", campaign.name);
        setSelectedCampaignDetails(campaign);
        setIsModalOpen(true);
        
        // Add a slight delay before adding the active class for animation
        setTimeout(() => {
            if (modalRef.current) {
                modalRef.current.classList.add('active');
            }
        }, 10);
    }, []);

    // Handler to close the modal
    const closeModal = useCallback(() => {
        if (modalRef.current) {
            modalRef.current.classList.remove('active');
            
            // Wait for animation to complete before removing modal
            setTimeout(() => {
                setIsModalOpen(false);
            }, 400);
        } else {
            setIsModalOpen(false);
        }
    }, []);

    // Handler for the final confirmation button
    const handleConfirmCampaign = () => {
        if (!selectedCampaignDetails) return;

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
        return (
            <div className="loading-container">
                <div className="spinner-border" role="status"></div>
                <div>Loading Campaigns...</div>
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
        <div className="step2-outer-container">
            {/* Title with subtle underline effect */}
            <h2 className="step2-title">Choose Your Campaign</h2>

            {/* Grid of Campaign Cards */}
            <div className="campaign-grid-container">
                {campaigns.map((campaign) => {
                    // Skip if campaign is invalid
                    if (!campaign) {
                        console.warn("Received null or undefined campaign in data");
                        return null;
                    }

                    // Get image URL if available
                    const backgroundImageUrl = campaign.image ? getFullImageUrl(campaign.image) : null;
                    
                    // Define background style with image or fallback gradient
                    const cardStyle = backgroundImageUrl
                        ? { backgroundImage: `url(${backgroundImageUrl})` }
                        : { backgroundImage: 'linear-gradient(135deg, #2a2a2a, #1a1a1a)' };

                    return (
                        <div
                            key={campaign.id}
                            className={`campaign-card ${selectedCampaignDetails?.id === campaign.id ? 'selected' : ''} ${campaign.is_default ? 'default-option' : ''}`}
                            onClick={() => handleCampaignSelect(campaign)}
                            style={cardStyle}
                        >
                            {/* Content inside card */}
                            <div className="campaign-card-content">
                                <h3 className="campaign-card-title">{campaign.name || "Unnamed Campaign"}</h3>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Details Modal - Conditionally Rendered */}
            {isModalOpen && (
                <div className="campaign-modal-overlay" ref={modalRef} onClick={closeModal}>
                    <div className="campaign-modal" onClick={(e) => e.stopPropagation()}>
                        <button className="modal-close-btn" onClick={closeModal}>×</button>
                        
                        {/* Campaign Image */}
                        {selectedCampaignDetails.image && (
                            <div className="modal-image-container">
                                <img 
                                    src={getFullImageUrl(selectedCampaignDetails.image)} 
                                    alt={selectedCampaignDetails.name} 
                                    className="modal-image"
                                />
                            </div>
                        )}
                        
                        <div className="modal-content">
                            {/* Campaign Title */}
                            <h2 className="modal-title">{selectedCampaignDetails.name || "Campaign Details"}</h2>
                            
                            {/* Campaign Description */}
                            <p className="modal-description">{selectedCampaignDetails.description || "No description available"}</p>
                            
                            <div className="modal-divider"></div>
                            
                            {/* Campaign Details in Card Format */}
                            <div className="modal-details">
                                {/* Length Detail */}
                                {selectedCampaignDetails.estimated_length && (
                                    <div className="detail-item">
                                        <div className="detail-label">Estimated Length</div>
                                        <div className="detail-value">{selectedCampaignDetails.estimated_length}</div>
                                    </div>
                                )}
                                
                                {/* Leveling Method */}
                                {selectedCampaignDetails.leveling && (
                                    <div className="detail-item">
                                        <div className="detail-label">Leveling Method</div>
                                        <div className="detail-value">{selectedCampaignDetails.leveling}</div>
                                    </div>
                                )}
                                
                                {/* Themes Display */}
                                {selectedCampaignDetails.themes && selectedCampaignDetails.themes.length > 0 && (
                                    <div className="detail-item">
                                        <div className="detail-label">Themes</div>
                                        <div className="themes-container">
                                            {selectedCampaignDetails.themes.map((theme, index) => (
                                                <span key={index} className="theme-tag">{theme}</span>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                            
                            {/* Confirm Button */}
                            <div className="confirm-button-container">
                                <button 
                                    className="confirm-campaign-btn"
                                    onClick={handleConfirmCampaign}
                                >
                                    Begin This Adventure
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Navigation Buttons */}
            <div className="step2-navigation">
                <button className="back-button" onClick={prevStep}>
                    <i className="bi bi-arrow-left"></i> Back to World Choice
                </button>
                
                {/* Optional: Add a Continue button that's enabled when a campaign is selected */}
                <button 
                    className={`continue-button ${selectedCampaignDetails ? 'active' : ''}`}
                    onClick={selectedCampaignDetails ? () => handleCampaignSelect(selectedCampaignDetails) : undefined}
                    disabled={!selectedCampaignDetails}
                >
                    View Selected Campaign <i className="bi bi-arrow-right"></i>
                </button>
            </div>
        </div>
    );
}

export default Step2_CampaignSelector;