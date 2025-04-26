// File: frontend/src/components/steps/Step9_EquipmentSelector.jsx

import React, { useState, useEffect, useRef } from 'react';
import './Step9_EquipmentSelector.css';

function Step9_EquipmentSelector({ characterData, updateCharacterData, nextStep, prevStep }) {
    const [equipmentOptions, setEquipmentOptions] = useState([]);
    const [backgroundEquipment, setBackgroundEquipment] = useState([]);
    const [selectedEquipment, setSelectedEquipment] = useState({});
    const [equipmentDetails, setEquipmentDetails] = useState({});
    const [activeItemDetails, setActiveItemDetails] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const [equipmentGroups, setEquipmentGroups] = useState([]);
    const [currentGroup, setCurrentGroup] = useState(0);
    const [optionsMade, setOptionsMade] = useState([]);
    
    // Ref for item details modal
    const itemDetailsRef = useRef(null);

    // Fetch equipment data
    useEffect(() => {
        if (!characterData.worldId || !characterData.classId) {
            setError("Missing required character data. Please complete previous steps.");
            setIsLoading(false);
            return;
        }

        setIsLoading(true);
        setError(null);
        
        // Fetch data from the API
        fetch(`/characters/api/creation-data/${characterData.worldId}`)
            .then(response => {
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                return response.json();
            })
            .then(data => {
                if (data.success && data.data) {
                    console.log("Creation data received:", data.data);
                    
                    // Find the class data for the selected class
                    const selectedClass = data.data.classes.find(c => c.id === characterData.classId);
                    
                    if (selectedClass && selectedClass.startingEquipment) {
                        // Get default equipment
                        const defaultItems = selectedClass.startingEquipment.default || [];
                        
                        // Process equipment options
                        const options = selectedClass.startingEquipment.options || [];
                        setEquipmentOptions(options);
                        
                        // Create equipment groups for selection UI
                        setEquipmentGroups(options.map((option, index) => ({
                            id: index,
                            name: `Equipment Option ${index + 1}`,
                            completed: false
                        })));
                        
                        // Get background equipment if available
                        if (characterData.backgroundId) {
                            const selectedBackground = data.data.backgrounds.find(b => b.id === characterData.backgroundId);
                            if (selectedBackground && selectedBackground.startingEquipment) {
                                setBackgroundEquipment(selectedBackground.startingEquipment);
                            }
                        }
                        
                        // Get equipment details from the API data
                        if (data.data.equipment) {
                            setEquipmentDetails(data.data.equipment);
                        }
                        
                        setIsLoading(false);
                    } else {
                        throw new Error(`Class ${characterData.classId} does not have starting equipment data.`);
                    }
                } else {
                    throw new Error(data.error || 'Invalid data format.');
                }
            })
            .catch(err => {
                console.error("Step9: Failed to fetch equipment data:", err);
                setError(`Failed to load equipment data: ${err.message}. Check your connection or try again later.`);
                setIsLoading(false);
            });
    }, [characterData.worldId, characterData.classId, characterData.backgroundId]);

    // Get item details from consolidated equipment data
    const getItemDetails = (itemId, type) => {
        if (!itemId) return null;
        
        // For debugging
        console.log("Looking up:", itemId, type);
        
        const normalizedId = itemId.toLowerCase().replace(/\s+/g, '_');
        let itemDetails = null;
        
        // For weapons (has extra nesting level)
        if (!itemDetails && (type === 'weapon' || !type)) {
            // Loop through each weapon category (simple_melee, martial_ranged, etc.)
            for (const category in equipmentDetails.weapons) {
                const weaponCategory = equipmentDetails.weapons[category];
                
                // Check if this category contains our item
                if (weaponCategory[normalizedId]) {
                    itemDetails = {
                        ...weaponCategory[normalizedId],
                        category: 'weapon',
                        subcategory: category
                    };
                    break;
                }
                
                // If not found by ID, try by name
                for (const weaponId in weaponCategory) {
                    const weapon = weaponCategory[weaponId];
                    if (weapon.name && weapon.name.toLowerCase() === itemId.toLowerCase()) {
                        itemDetails = {
                            ...weapon,
                            category: 'weapon',
                            subcategory: category
                        };
                        break;
                    }
                }
                
                if (itemDetails) break;
            }
        }
        
        // For armor (has extra nesting level)
        if (!itemDetails && (type === 'armor' || !type)) {
            for (const category in equipmentDetails.armor) {
                const armorCategory = equipmentDetails.armor[category];
                
                // Check if this category contains our item
                if (armorCategory[normalizedId]) {
                    itemDetails = {
                        ...armorCategory[normalizedId],
                        category: 'armor',
                        subcategory: category
                    };
                    break;
                }
                
                // If not found by ID, try by name
                for (const armorId in armorCategory) {
                    const armor = armorCategory[armorId];
                    if (armor.name && armor.name.toLowerCase() === itemId.toLowerCase()) {
                        itemDetails = {
                            ...armor,
                            category: 'armor',
                            subcategory: category
                        };
                        break;
                    }
                }
                
                if (itemDetails) break;
            }
        }
        
        // For packs (direct top-level items)
        if (!itemDetails && (type === 'pack' || !type)) {
            if (equipmentDetails.packs[normalizedId]) {
                itemDetails = {
                    ...equipmentDetails.packs[normalizedId],
                    category: 'pack'
                };
            } else {
                // Try by name
                for (const packId in equipmentDetails.packs) {
                    const pack = equipmentDetails.packs[packId];
                    if (pack.name && pack.name.toLowerCase() === itemId.toLowerCase()) {
                        itemDetails = {
                            ...pack,
                            category: 'pack'
                        };
                        break;
                    }
                }
            }
        }
        
        // For gear (direct top-level items)
        if (!itemDetails && (type === 'gear' || !type)) {
            if (equipmentDetails.gear[normalizedId]) {
                itemDetails = {
                    ...equipmentDetails.gear[normalizedId],
                    category: 'gear'
                };
            } else {
                // Try by name
                for (const gearId in equipmentDetails.gear) {
                    const gear = equipmentDetails.gear[gearId];
                    if (gear.name && gear.name.toLowerCase() === itemId.toLowerCase()) {
                        itemDetails = {
                            ...gear,
                            category: 'gear'
                        };
                        break;
                    }
                }
            }
        }
        
        // Special case for compound items
        if (!itemDetails && itemId.includes(" and ")) {
            const parts = itemId.split(" and ").map(part => part.trim());
            return {
                name: itemId,
                description: `This equipment consists of: ${parts.join(" and ")}.`,
                category: type || 'equipment',
                compound: true
            };
        }
        
        if (!itemDetails) {
            console.warn(`No details found for item: ${itemId}`);
        }
        
        return itemDetails;
    };       

    // Helper function to normalize equipment items
    const normalizeEquipmentItem = (item) => {
        // If item is a string, convert to object with item property
        if (typeof item === 'string') {
            return { item: item, type: 'equipment' };
        }
        
        // If item is already an object
        if (typeof item === 'object' && item !== null) {
            // Make sure it has the item property
            if (!item.item && item.name) {
                // If it has name but no item, use name as item
                return { ...item, item: item.name };
            }
            
            // If it has neither item nor name, create a placeholder
            if (!item.item && !item.name) {
                console.warn("Found equipment item without name or item property:", item);
                return { 
                    item: item.id || "Unnamed Item",
                    type: item.type || "equipment" 
                };
            }
            
            // If it already has item property, return as is
            return item;
        }
        
        // Fallback for any unexpected values
        console.warn("Found unexpected equipment item format:", item);
        return { item: "Unknown Item", type: "equipment" };
    };

    // Handler for selecting equipment option
    const handleOptionSelect = (optionIndex, choiceIndex) => {
        // Update selected equipment
        setSelectedEquipment(prev => ({
            ...prev,
            [optionIndex]: choiceIndex
        }));
        
        // Mark this group as completed
        setOptionsMade(prev => {
            if (!prev.includes(optionIndex)) {
                return [...prev, optionIndex];
            }
            return prev;
        });
        
        // Update equipment groups
        setEquipmentGroups(prev => 
            prev.map((group, idx) => 
                idx === optionIndex 
                    ? { ...group, completed: true }
                    : group
            )
        );
        
        // Move to next group if available
        if (currentGroup < equipmentGroups.length - 1) {
            setCurrentGroup(currentGroup + 1);
        }
    };

    // Handler for showing item details
    const handleShowDetails = (item, e) => {
        // If the event is provided, prevent it from bubbling up to parent elements
        if (e) {
            e.stopPropagation();
        }
        
        // Get full item details from our consolidated data
        const details = getItemDetails(item.id || item.item, item.type);
        
        if (details) {
            setActiveItemDetails({
                ...item,
                details
            });
            
            // Add a slight delay before adding the active class for animation
            setTimeout(() => {
                if (itemDetailsRef.current) {
                    itemDetailsRef.current.classList.add('active');
                }
            }, 10);
        } else {
            console.warn(`No details found for item: ${item.item || item.id}`);
        }
    };

    // Handler for closing item details
    const handleCloseDetails = () => {
        if (itemDetailsRef.current) {
            itemDetailsRef.current.classList.remove('active');
            
            // Wait for animation to complete before removing modal
            setTimeout(() => {
                setActiveItemDetails(null);
            }, 400);
        } else {
            setActiveItemDetails(null);
        }
    };

    // Navigate between equipment groups
    const navigateGroup = (direction) => {
        if (direction === 'prev' && currentGroup > 0) {
            setCurrentGroup(currentGroup - 1);
        } else if (direction === 'next' && currentGroup < equipmentGroups.length - 1) {
            setCurrentGroup(currentGroup + 1);
        }
    };

    // Validate equipment selections
    const validateSelections = () => {
        // Check if all required choices are made
        if (optionsMade.length < equipmentOptions.length) {
            return {
                valid: false,
                message: `Please make selections for all equipment options.`
            };
        }
        
        return { valid: true };
    };

    // Handle continue button
    const handleContinue = () => {
        const validation = validateSelections();
        
        if (!validation.valid) {
            alert(validation.message);
            return;
        }
        
        // Convert selected equipment options to actual equipment list
        const equippedItems = [];
        
        // Add items from class equipment choices
        equipmentOptions.forEach((optionGroup, groupIndex) => {
            const selectedChoice = selectedEquipment[groupIndex];
            
            if (selectedChoice !== undefined) {
                const choice = optionGroup.group || optionGroup;
                if (Array.isArray(choice)) {
                    // If direct array of options
                    const selectedItem = choice[selectedChoice];
                    if (selectedItem) {
                        equippedItems.push(normalizeEquipmentItem(selectedItem));
                    }
                } else if (selectedChoice === 0 && optionGroup.group) {
                    // First option (group)
                    optionGroup.group.forEach(item => {
                        if (item) {
                            equippedItems.push(normalizeEquipmentItem(item));
                        }
                    });
                } else if (selectedChoice === 1 && optionGroup.or) {
                    // Second option (or)
                    optionGroup.or.forEach(item => {
                        if (item) {
                            equippedItems.push(normalizeEquipmentItem(item));
                        }
                    });
                }
            }
        });
        
        // Add default equipment from class
        const selectedClass = characterData.classId;
        if (selectedClass && equipmentOptions.default) {
            equipmentOptions.default.forEach(item => {
                if (item) {
                    equippedItems.push(normalizeEquipmentItem(item));
                }
            });
        }
        
        // Add background equipment
        backgroundEquipment.forEach(item => {
            if (item) {
                equippedItems.push(normalizeEquipmentItem(item));
            }
        });
        
        console.log("Final equipped items:", equippedItems);
        
        // Update character data with selected equipment
        updateCharacterData({
            equipment: {
                equipped: equippedItems,
                selections: selectedEquipment
            }
        });
        
        // Move to next step
        nextStep();
    };

    // Render equipment option
    const renderEquipmentOption = (option, optionIndex) => {
        // Get current option group
        const currentOption = equipmentOptions[currentGroup];
        
        // Check if this is the current group
        if (optionIndex !== currentGroup) {
            return null;
        }
        
        // Render option cards
        return (
            <div className="equipment-option-container" key={optionIndex}>
                <h3 className="option-title">Choose One Option:</h3>
                
                <div className="equipment-option-grid">
                    {/* First option (group) */}
                    {currentOption.group && (
                        <div 
                            className={`equipment-option-card ${selectedEquipment[optionIndex] === 0 ? 'selected' : ''}`}
                            onClick={() => handleOptionSelect(optionIndex, 0)}
                        >
                            <h4 className="option-name">Option 1</h4>
                            <div className="equipment-items-list">
                                {currentOption.group.map((item, idx) => (
                                    <div className="equipment-item" key={idx}>
                                        <span className="item-name">{item.item}</span>
                                        <span className="item-type">{item.type}</span>
                                        <button 
                                            className="details-button"
                                            onClick={(e) => {
                                                // Stop propagation to prevent triggering the parent's onClick
                                                e.stopPropagation();
                                                handleShowDetails(item, e);
                                            }}
                                        >
                                            <i className="bi bi-info-circle"></i>
                                        </button>
                                    </div>
                                ))}
                            </div>
                            <div className="selected-indicator">
                                <i className="bi bi-check-circle-fill"></i> Selected
                            </div>
                        </div>
                    )}
                    
                    {/* Second option (or) */}
                    {currentOption.or && (
                        <div 
                            className={`equipment-option-card ${selectedEquipment[optionIndex] === 1 ? 'selected' : ''}`}
                            onClick={() => handleOptionSelect(optionIndex, 1)}
                        >
                            <h4 className="option-name">Option 2</h4>
                            <div className="equipment-items-list">
                                {currentOption.or.map((item, idx) => (
                                    <div className="equipment-item" key={idx}>
                                        <span className="item-name">{item.item}</span>
                                        <span className="item-type">{item.type}</span>
                                        <button 
                                            className="details-button"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleShowDetails(item);
                                            }}
                                        >
                                            <i className="bi bi-info-circle"></i>
                                        </button>
                                    </div>
                                ))}
                            </div>
                            <div className="selected-indicator">
                                <i className="bi bi-check-circle-fill"></i> Selected
                            </div>
                        </div>
                    )}
                </div>
            </div>
        );
    };

    // Render equipment group navigation
    const renderGroupNavigation = () => {
        return (
            <div className="equipment-group-navigation">
                <button 
                    className="prev-group-btn"
                    onClick={() => navigateGroup('prev')}
                    disabled={currentGroup === 0}
                >
                    <i className="bi bi-arrow-left"></i> Previous Option
                </button>
                
                <div className="group-indicators">
                    {equipmentGroups.map((group, idx) => (
                        <div 
                            key={idx} 
                            className={`group-indicator ${idx === currentGroup ? 'active' : ''} ${group.completed ? 'completed' : ''}`}
                            onClick={() => setCurrentGroup(idx)}
                        >
                            {group.completed && <i className="bi bi-check-circle-fill"></i>}
                        </div>
                    ))}
                </div>
                
                <button 
                    className="next-group-btn"
                    onClick={() => navigateGroup('next')}
                    disabled={currentGroup === equipmentGroups.length - 1}
                >
                    Next Option <i className="bi bi-arrow-right"></i>
                </button>
            </div>
        );
    };

    // --- Render Logic ---
    if (isLoading) {
        return (
            <div className="loading-container">
                <div className="spinner-border" role="status"></div>
                <div>Loading Equipment Options...</div>
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
        <div className="step9-outer-container">
            {/* Title */}
            <h2 className="step9-title">Starting Equipment</h2>
            
            {/* Equipment Selection Explanation */}
            <div className="equipment-explanation">
                <h3>Choose Your Starting Equipment</h3>
                <p>
                    Your class ({characterData.className}) provides you with starting equipment options.
                    Make a selection for each category below.
                </p>
                <p>
                    {backgroundEquipment.length > 0 && 
                        `Your background (${characterData.backgroundName}) also provides additional equipment that will be added automatically.`}
                </p>
            </div>
            
            {/* Equipment Group Navigation */}
            {equipmentGroups.length > 1 && renderGroupNavigation()}
            
            {/* Equipment Selection */}
            <div className="equipment-selection-container">
                {equipmentOptions.map((option, idx) => renderEquipmentOption(option, idx))}
            </div>
            
            {/* Equipment Summary (background and default items) */}
            <div className="equipment-summary-container">
                <h3 className="summary-title">Additional Equipment</h3>
                <p className="summary-description">
                    These items will be added automatically to your character's equipment.
                </p>
                
                <div className="default-equipment-section">
                    <h4>Class Equipment</h4>
                    <div className="default-equipment-list">
                        {equipmentOptions[0]?.default?.map((item, idx) => (
                            <div className="default-equipment-item" key={idx}>
                                <span className="item-name">{item.item}</span>
                                <span className="item-type">{item.type}</span>
                                <button 
                                    className="details-button"
                                    onClick={() => handleShowDetails(item)}
                                >
                                    <i className="bi bi-info-circle"></i>
                                </button>
                            </div>
                        ))}
                    </div>
                </div>
                
                {backgroundEquipment.length > 0 && (
                    <div className="background-equipment-section">
                        <h4>Background Equipment</h4>
                        <div className="background-equipment-list">
                            {backgroundEquipment.map((item, idx) => (
                                <div className="background-equipment-item" key={idx}>
                                    <span className="item-name">{typeof item === 'string' ? item : item.item}</span>
                                    <button 
                                        className="details-button"
                                        onClick={() => handleShowDetails(typeof item === 'string' ? { item } : item)}
                                    >
                                        <i className="bi bi-info-circle"></i>
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
            
            {/* Item Details Modal */}
            {activeItemDetails && (
                <div 
                    className="item-details-overlay" 
                    ref={itemDetailsRef} 
                    onClick={handleCloseDetails}
                >
                    <div className="item-details-modal" onClick={(e) => e.stopPropagation()}>
                        <button className="close-button" onClick={handleCloseDetails}>×</button>
                        
                        <div className="item-details-header">
                            <h3 className="item-details-name">
                                {activeItemDetails.details?.name || activeItemDetails.item}
                            </h3>
                            <div className="item-details-type">
                                {activeItemDetails.details?.category || activeItemDetails.type || "Item"}
                            </div>
                        </div>
                        
                        <div className="item-details-content">
                            {/* Item properties based on type */}
                            {activeItemDetails.details && (
                                <div className="item-properties">
                                    {/* Weapon properties */}
                                    {activeItemDetails.details.damage && (
                                        <div className="item-property">
                                            <span className="property-label">Damage:</span>
                                            <span className="property-value">
                                                {activeItemDetails.details.damage} {activeItemDetails.details.damage_type}
                                            </span>
                                        </div>
                                    )}
                                    
                                    {/* Weapon range */}
                                    {activeItemDetails.details.range && (
                                        <div className="item-property">
                                            <span className="property-label">Range:</span>
                                            <span className="property-value">
                                                {activeItemDetails.details.range}
                                            </span>
                                        </div>
                                    )}
                                    
                                    {/* Armor properties */}
                                    {activeItemDetails.details.armor_class && (
                                        <div className="item-property">
                                            <span className="property-label">Armor Class:</span>
                                            <span className="property-value">
                                                {activeItemDetails.details.armor_class} + Dex modifier
                                                {activeItemDetails.details.max_dex_bonus && 
                                                    ` (max +${activeItemDetails.details.max_dex_bonus})`}
                                            </span>
                                        </div>
                                    )}
                                    
                                    {/* Shield AC bonus */}
                                    {activeItemDetails.details.armor_class_bonus && (
                                        <div className="item-property">
                                            <span className="property-label">AC Bonus:</span>
                                            <span className="property-value">
                                                +{activeItemDetails.details.armor_class_bonus}
                                            </span>
                                        </div>
                                    )}
                                    
                                    {/* Strength requirement */}
                                    {activeItemDetails.details.strength_requirement && (
                                        <div className="item-property">
                                            <span className="property-label">Strength Required:</span>
                                            <span className="property-value">
                                                {activeItemDetails.details.strength_requirement}
                                            </span>
                                        </div>
                                    )}
                                    
                                    {/* Stealth disadvantage */}
                                    {activeItemDetails.details.stealth_disadvantage && (
                                        <div className="item-property">
                                            <span className="property-label">Stealth:</span>
                                            <span className="property-value">
                                                Disadvantage
                                            </span>
                                        </div>
                                    )}
                                    
                                    {/* Common properties */}
                                    {activeItemDetails.details.weight && (
                                        <div className="item-property">
                                            <span className="property-label">Weight:</span>
                                            <span className="property-value">
                                                {activeItemDetails.details.weight}
                                            </span>
                                        </div>
                                    )}
                                    
                                    {activeItemDetails.details.cost && (
                                        <div className="item-property">
                                            <span className="property-label">Cost:</span>
                                            <span className="property-value">
                                                {activeItemDetails.details.cost}
                                            </span>
                                        </div>
                                    )}
                                    
                                    {/* Properties list for weapons */}
                                    {activeItemDetails.details.properties && (
                                        <div className="item-property">
                                            <span className="property-label">Properties:</span>
                                            <span className="property-value">
                                                {Array.isArray(activeItemDetails.details.properties) 
                                                    ? activeItemDetails.details.properties.join(', ')
                                                    : activeItemDetails.details.properties}
                                            </span>
                                        </div>
                                    )}
                                    
                                    {/* Pack contents */}
                                    {activeItemDetails.details.contents && (
                                        <div className="item-property pack-contents">
                                            <span className="property-label">Contains:</span>
                                            <ul className="pack-contents-list">
                                                {Object.entries(activeItemDetails.details.contents).map(([item, quantity], idx) => (
                                                    <li key={idx}>
                                                        {typeof quantity === 'number' ? `${quantity} × ` : ''} 
                                                        {typeof item === 'string' ? item.replace(/_/g, ' ') : item}
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                </div>
                            )}
                            
                            {/* Item description */}
                            <div className="item-description">
                                {activeItemDetails.details?.description || 
                                    "No detailed information available for this item."}
                            </div>
                        </div>
                    </div>
                </div>
            )}
            
            {/* Navigation Buttons */}
            <div className="step9-navigation">
                <button className="back-button" onClick={prevStep}>
                    <i className="bi bi-arrow-left"></i> Back to Skills
                </button>
                
                <button 
                    className={`continue-button ${validateSelections().valid ? 'active' : ''}`}
                    onClick={handleContinue}
                    disabled={!validateSelections().valid}
                >
                    Continue to Alignment <i className="bi bi-arrow-right"></i>
                </button>
            </div>
        </div>
    );
}

export default Step9_EquipmentSelector;