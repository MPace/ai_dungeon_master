// File: frontend/src/components/steps/Step3_ClassSelector.jsx

import React, { useState, useEffect, useCallback, useRef } from 'react';
import './Step3_ClassSelector.css';

function Step3_ClassSelector({ characterData, updateCharacterData, nextStep, prevStep }) {
    const [classes, setClasses] = useState([]);
    const [selectedClassDetails, setSelectedClassDetails] = useState(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    
    // Ref for modal
    const modalRef = useRef(null);

    // Fetch classes for the selected world
    useEffect(() => {
        if (!characterData.worldId) {
            setError("No world selected. Please go back to Step 1.");
            setIsLoading(false);
            return;
        }

        setIsLoading(true);
        setError(null);
        
        // Fetch classes from the API (using the world ID to filter allowed classes)
        fetch(`/characters/api/creation-data/${characterData.worldId}`)
            .then(response => {
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                return response.json();
            })
            .then(data => {
                if (data.success && data.data && Array.isArray(data.data.classes)) {
                    // Log the classes we received to help debug the paladin issue
                    console.log("Classes received:", data.data.classes.map(c => c.id));
                    setClasses(data.data.classes);
                    setIsLoading(false);
                } else {
                    throw new Error(data.error || 'Invalid data format for classes.');
                }
            })
            .catch(err => {
                console.error("Step3: Failed to fetch classes:", err);
                setError(`Failed to load classes: ${err.message}. Check your connection or try again later.`);
                setIsLoading(false);
            });
    }, [characterData.worldId]);

    // Helper to get the full image URL
    const getImageUrl = useCallback((imagePath) => {
        if (!imagePath) return null;
        
        // If it's already a full URL (http or https), use it directly
        if (imagePath.startsWith('http://') || imagePath.startsWith('https://')) {
            return imagePath;
        }
        
        // Handle relative paths by adding the static prefix
        return `/static/build/${imagePath.startsWith('/') ? imagePath.substring(1) : imagePath}`;
    }, []);

    // Handler when a class card is clicked
    const handleClassSelect = useCallback((classData) => {
        console.log("Class selected for details view:", classData.name);
        setSelectedClassDetails(classData);
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
    const handleConfirmClass = () => {
        if (!selectedClassDetails) return;

        console.log(`Class confirmed: ${selectedClassDetails.name}`);
        updateCharacterData({
            classId: selectedClassDetails.id,
            className: selectedClassDetails.name,
            // Reset subsequent steps if necessary
            raceId: null,
            raceName: null,
            backgroundId: null,
            backgroundName: null
        });
        nextStep();
    };

    // --- Render Logic ---
    if (isLoading) {
        return (
            <div className="loading-container">
                <div className="spinner-border" role="status"></div>
                <div>Loading Classes...</div>
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
        <div className="step3-outer-container">
            {/* Title with subtle underline effect */}
            <h2 className="step3-title">Choose Your Class</h2>

            {/* Grid of Class Cards */}
            <div className="class-grid-container">
                {classes.map((classData) => {
                    // Skip if class data is invalid
                    if (!classData) {
                        console.warn("Received null or undefined class in data");
                        return null;
                    }

                    // Log each class to debug paladin issue
                    console.log(`Rendering class card: ${classData.id} - ${classData.name}`);

                    return (
                        <div
                            key={classData.id}
                            className={`class-card ${selectedClassDetails?.id === classData.id ? 'selected' : ''}`}
                            onClick={() => handleClassSelect(classData)}
                        >
                            {/* Class icon or symbol */}
                            <div className="class-icon">
                                <i className={`bi bi-${classData.icon || 'shield'}`}></i>
                            </div>
                            
                            {/* Class name and brief description */}
                            <h3 className="class-name">{classData.name}</h3>
                            <div className="class-description">{classData.shortDescription}</div>
                        </div>
                    );
                })}
            </div>

            {/* Class Details Modal - Conditionally Rendered */}
            {isModalOpen && selectedClassDetails && (
                <div className="class-modal-overlay" ref={modalRef} onClick={closeModal}>
                    <div className="class-modal" onClick={(e) => e.stopPropagation()}>
                        <button className="modal-close-btn" onClick={closeModal}>×</button>
                        
                        {/* Class header section */}
                        <div className="class-modal-header">
                            <div className="class-modal-icon">
                                <i className={`bi bi-${selectedClassDetails.icon || 'shield'}`}></i>
                            </div>
                            <h2 className="class-modal-title">{selectedClassDetails.name}</h2>
                        </div>
                        
                        {/* Class image */}
                        {selectedClassDetails.image && (
                            <div className="class-image-container">
                                <img 
                                    src={getImageUrl(selectedClassDetails.image)} 
                                    alt={selectedClassDetails.name} 
                                    className="class-image"
                                />
                            </div>
                        )}
                        
                        <div className="class-modal-content">
                            {/* Class description */}
                            <p className="class-full-description">{selectedClassDetails.description}</p>
                            
                            <div className="class-details-grid">
                                {/* Core class mechanics */}
                                <div className="class-detail-card">
                                    <h4 className="detail-title">Class Features</h4>
                                    <div className="detail-content">
                                        <div className="feature-row">
                                            <span className="feature-label">Hit Die:</span>
                                            <span className="feature-value">{selectedClassDetails.hitDie}</span>
                                        </div>
                                        <div className="feature-row">
                                            <span className="feature-label">Primary Ability:</span>
                                            <span className="feature-value">{selectedClassDetails.primaryAbility}</span>
                                        </div>
                                        {selectedClassDetails.secondaryAbility && (
                                            <div className="feature-row">
                                                <span className="feature-label">Secondary:</span>
                                                <span className="feature-value">{selectedClassDetails.secondaryAbility}</span>
                                            </div>
                                        )}
                                        <div className="feature-row">
                                            <span className="feature-label">Saving Throws:</span>
                                            <span className="feature-value">
                                                {Array.isArray(selectedClassDetails.savingThrows) 
                                                    ? selectedClassDetails.savingThrows.join(', ') 
                                                    : selectedClassDetails.savingThrows}
                                            </span>
                                        </div>
                                        <div className="feature-row">
                                            <span className="feature-label">Armor:</span>
                                            <span className="feature-value">{selectedClassDetails.armorProficiency}</span>
                                        </div>
                                        <div className="feature-row">
                                            <span className="feature-label">Weapons:</span>
                                            <span className="feature-value">{selectedClassDetails.weaponProficiency}</span>
                                        </div>
                                    </div>
                                </div>
                                
                                {/* Class abilities at level 1 */}
                                <div className="class-detail-card">
                                    <h4 className="detail-title">1st Level Abilities</h4>
                                    <div className="detail-content">
                                        {selectedClassDetails.features?.level1?.map((ability, index) => (
                                            <div key={index} className="ability-item">
                                                <div className="ability-name">{ability.name}</div>
                                                <div className="ability-desc">{ability.description}</div>
                                                {ability.type && (
                                                    <div className="ability-type">
                                                        {ability.type === 'active' ? 'Active Ability' : 'Passive Ability'}
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                                
                                {/* Playstyle section */}
                                <div className="class-detail-card">
                                    <h4 className="detail-title">Playstyle</h4>
                                    <div className="detail-content">
                                        <p className="playstyle-desc">{selectedClassDetails.playstyle}</p>
                                        
                                        {/* Playstyle tags */}
                                        {Array.isArray(selectedClassDetails.tags) && (
                                            <div className="playstyle-tags">
                                                {selectedClassDetails.tags.map((tag, index) => (
                                                    <span key={index} className="playstyle-tag">{tag}</span>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                            
                            {/* Starting Equipment Section */}
                            {selectedClassDetails.startingEquipment && (
                                <div className="equipment-section">
                                    <h4 className="section-title">Starting Equipment</h4>
                                    <p className="section-desc">As a {selectedClassDetails.name}, you start with the following equipment options:</p>
                                    
                                    {/* Equipment Options */}
                                    <div className="equipment-options">
                                        {selectedClassDetails.startingEquipment.options?.map((option, optIndex) => (
                                            <div key={optIndex} className="equipment-option">
                                                <span className="option-number">{optIndex + 1}.</span>
                                                {option.group && (
                                                    <span className="option-items">
                                                        {option.group.map(item => item.item).join(', ')}
                                                    </span>
                                                )}
                                                {option.or && (
                                                    <span className="option-or">
                                                        OR {option.or.map(item => item.item).join(', ')}
                                                    </span>
                                                )}
                                            </div>
                                        ))}
                                        {/* Default equipment that everyone gets */}
                                        {selectedClassDetails.startingEquipment.default?.length > 0 && (
                                            <div className="default-equipment">
                                                <span className="default-label">You also get:</span>
                                                <span className="default-items">
                                                    {selectedClassDetails.startingEquipment.default.map(item => item.item).join(', ')}
                                                </span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}
                            
                            {/* Confirm Button */}
                            <div className="confirm-button-container">
                                <button 
                                    className="confirm-class-btn"
                                    onClick={handleConfirmClass}
                                >
                                    Choose {selectedClassDetails.name}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Navigation Buttons */}
            <div className="step3-navigation">
                <button className="back-button" onClick={prevStep}>
                    <i className="bi bi-arrow-left"></i> Back to Campaign
                </button>
                
                {/* Continue button that's enabled when a class is selected */}
                <button 
                    className={`continue-button ${selectedClassDetails ? 'active' : ''}`}
                    onClick={selectedClassDetails ? handleConfirmClass : undefined}
                    disabled={!selectedClassDetails}
                >
                    Continue with {selectedClassDetails ? selectedClassDetails.name : 'Selected Class'} <i className="bi bi-arrow-right"></i>
                </button>
            </div>
        </div>
    );
}

export default Step3_ClassSelector;