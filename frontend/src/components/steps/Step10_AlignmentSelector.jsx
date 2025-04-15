// File: frontend/src/components/steps/Step10_AlignmentSelector.jsx

import React, { useState, useRef } from 'react';
import './Step10_AlignmentSelector.css';

function Step10_AlignmentSelector({ characterData, updateCharacterData, nextStep, prevStep }) {
    const [selectedAlignment, setSelectedAlignment] = useState(characterData.alignment || null);
    const [activeDetails, setActiveDetails] = useState(null);
    
    // Ref for alignment details modal
    const detailsModalRef = useRef(null);
    
    // Alignment data
    const alignments = [
        {
            id: 'lawful_good',
            name: 'Lawful Good',
            description: 'Follows rules and traditions with honor, and works to protect the innocent and uphold justice.',
            examples: 'A noble paladin who upholds the law while defending the weak.',
            axis: 'lawful',
            morality: 'good',
            details: 'Lawful Good characters believe in honor, duty, compassion, and order. They uphold rules and traditions but always with the goal of promoting the greater good. They defend the innocent, keep their word, and take responsibility seriously.',
            characters: ['Paladins', 'Loyal knights', 'Honest officials', 'Righteous clergy'],
            fullDescription: 'Lawful Good characters combine a commitment to oppose evil with the discipline to fight that evil with honor. They tell the truth, keep their word, help those in need, and speak out against injustice. A Lawful Good character hates to see the guilty go unpunished, but will maintain their own honor above all. Justice tempered with mercy is their guiding principle.'
        },
        {
            id: 'neutral_good',
            name: 'Neutral Good',
            description: 'Does good without bias toward law or chaos, helping others according to their needs.',
            examples: 'A village healer who cares for anyone who requires aid.',
            axis: 'neutral-axis',
            morality: 'good',
            details: 'Neutral Good characters do the best they can to help others and promote the welfare of all. They value both personal freedom and compassion, working with established systems when needed but being willing to work outside them when those systems don\'t fulfill their moral needs.',
            characters: ['Folk heroes', 'Most healers', 'Kind wizards', 'Charitable merchants'],
            fullDescription: 'Neutral Good characters are committed to helping others. They work with kings and magistrates but don\'t feel beholden to them. They have no problems with committing minor infractions if it serves the greater good, but avoid extreme measures when possible. These characters are pure altruists who believe in all the virtues of goodness without particular attachment to order or freedom.'
        },
        {
            id: 'chaotic_good',
            name: 'Chaotic Good',
            description: 'Values freedom and doing what\'s right over rules and laws, follows their own moral compass.',
            examples: 'A freedom fighter who opposes injustice through unconventional means.',
            axis: 'chaotic',
            morality: 'good',
            details: 'Chaotic Good characters act according to their conscience with little regard for what others expect. They believe in goodness and right but have little use for laws and regulations, following their own moral compass that may not align with society.',
            characters: ['Freedom fighters', 'Robin Hood-like bandits', 'Rebels with causes', 'Free-spirited bards'],
            fullDescription: 'Chaotic Good characters value both the welfare of all sentient life and the freedom of the individual. They believe laws exist to serve the people, not the other way around, and break laws they see as unjust. They follow their hearts and generally act with empathy and benevolence, but rarely submit to a governing authority they disagree with.'
        },
        {
            id: 'lawful_neutral',
            name: 'Lawful Neutral',
            description: 'Values order and organization above all else, following laws or personal codes without moral bias.',
            examples: 'A judge who follows the letter of the law without exceptions.',
            axis: 'lawful',
            morality: 'neutral-morality',
            details: 'Lawful Neutral characters act in accordance with law, tradition, or personal codes, believing that order benefits everyone in the long run. They are reliable, honorable, and follow rules without partisanship or bias for good or evil.',
            characters: ['Disciplined monks', 'Stern judges', 'Professional soldiers', 'Devoted traditionalists'],
            fullDescription: 'Lawful Neutral characters believe in order—in rules, traditions, hierarchies, and laws. These characters are bound by honor and duty, valuing stability and predictability. They value the rule of law, authority, and structure, sometimes placing them above any personal desire to do good or evil. To them, the means justify the ends if the means promote consistency and order.'
        },
        {
            id: 'true_neutral',
            name: 'True Neutral',
            description: 'Believes in the natural balance, takes no strong positions, and may act pragmatically based on the situation.',
            examples: 'A druid who views both civilization and wilderness as necessary parts of the natural order.',
            axis: 'neutral-axis',
            morality: 'neutral-morality',
            details: 'True Neutral characters do what seems like a good idea at the time, seeking to preserve balance above all. They don\'t feel strongly about causes or ideals and may be more pragmatic than passionate in their approach to life.',
            characters: ['Most animals', 'Pragmatic druids', 'Undecided individuals', 'Nature spirits'],
            fullDescription: 'True Neutral characters seek to maintain the balance and avoid extremes. They may be committed to a balance between the alignments as a philosophy or simply be apathetic and uncommitted to any moral stance. These characters often work on behalf of nature, which embodies the ultimate balance, as many druids do. Others are simply self-reliant and uninterested in moral judgments.'
        },
        {
            id: 'chaotic_neutral',
            name: 'Chaotic Neutral',
            description: 'Values personal freedom and follows whims, disliking authority and tradition but not deliberately cruel.',
            examples: 'A wandering bard who travels where the wind takes them, breaking local customs but not being malicious.',
            axis: 'chaotic',
            morality: 'neutral-morality',
            details: 'Chaotic Neutral characters follow their whims, valuing their freedom more than anything else. They are individualists first and foremost, strongly resisting external pressures to behave in a particular way.',
            characters: ['Free spirits', 'Wanderers', 'Unpredictable rogues', 'Eccentric artists'],
            fullDescription: 'Chaotic Neutral characters believe in the power of the individual over any society or group. They value their freedom and may even make sacrifices to preserve it, but generally avoid taking sides in conflicts involving good vs. evil. While they dislike rules, restrictions, and authorities, they don\'t typically act maliciously or go out of their way to disrupt organizations or harm innocents.'
        },
        {
            id: 'lawful_evil',
            name: 'Lawful Evil',
            description: 'Works within systems and traditions to achieve their selfish goals, using law to control others.',
            examples: 'A tyrannical ruler who maintains strict societal structure to maintain power.',
            axis: 'lawful',
            morality: 'evil',
            details: 'Lawful Evil characters methodically take what they want within the limits of their code of conduct or the laws of their society. They care about tradition, loyalty, and order—but not freedom, dignity, or life. They use society and its laws for their own ends.',
            characters: ['Tyrants', 'Devils', 'Corrupt officials', 'Guild leaders who exploit members'],
            fullDescription: 'Lawful Evil characters methodically take what they want from others while following the rules. They care about honor, tradition, and order but not about freedom or the welfare of others. They play by the rules, but without mercy or compassion, and within those rules, they do whatever they can to advance themselves. These characters value both control and tradition, using established rules to get their way.'
        },
        {
            id: 'neutral_evil',
            name: 'Neutral Evil',
            description: 'Pursues their own interests without compassion or moral principles, doing whatever they can get away with.',
            examples: 'A mercenary who takes any job regardless of ethics, only caring about payment.',
            axis: 'neutral-axis',
            morality: 'evil',
            details: 'Neutral Evil characters do whatever they can get away with, without any particular loyalty or respect for laws. They are self-centered and have no qualms about betraying others. They lack the discipline to be lawful and the wildness to be chaotic.',
            characters: ['Mercenaries without scruples', 'Power-hungry wizards', 'Opportunistic thieves', 'Uncaring backstabbers'],
            fullDescription: 'Neutral Evil characters are primarily concerned with themselves and their own advancement. They show no allegiance to laws or chaos, following whatever path gives them what they desire. These characters do not hesitate to betray allies and break deals when it suits them. Their goal is to get what they want, by any means that they can get away with. They are the essence of pure selfishness.'
        },
        {
            id: 'chaotic_evil',
            name: 'Chaotic Evil',
            description: 'Acts with arbitrary violence and destructiveness, driven by greed, hatred, or bloodlust.',
            examples: 'A demon who delights in destruction and pain for its own sake.',
            axis: 'chaotic',
            morality: 'evil',
            details: 'Chaotic Evil characters act with arbitrary violence, hate order, enjoy inflicting suffering, and possess no respect for rules, their lives, or the lives of others. They are completely selfish and view others as tools to use or victims to prey upon.',
            characters: ['Violent marauders', 'Many demons', 'Unpredictable monsters', 'Destructive zealots'],
            fullDescription: "Chaotic Evil characters act with arbitrary violence and destructive impulses. They have no respect for rules, their own lives, or the lives of anyone else. They take pleasure in the suffering of others and have no regard for honor, trust or the welfare of society. These characters are the most dangerous because they're motivated by whim and impulse, with no rules to predict or limit their behavior."
        }
    ];

    // Handler for selecting an alignment
    const handleSelectAlignment = (alignmentId) => {
        setSelectedAlignment(alignmentId);
    };

    // Handler for showing alignment details
    const handleShowDetails = (alignment, e) => {
        // If the event is provided, prevent it from bubbling up
        if (e) {
            e.stopPropagation();
        }
        
        setActiveDetails(alignment);
        
        // Add a slight delay before adding the active class for animation
        setTimeout(() => {
            if (detailsModalRef.current) {
                detailsModalRef.current.classList.add('active');
            }
        }, 10);
    };

    // Handler for closing alignment details
    const handleCloseDetails = () => {
        if (detailsModalRef.current) {
            detailsModalRef.current.classList.remove('active');
            
            // Wait for animation to complete before removing modal
            setTimeout(() => {
                setActiveDetails(null);
            }, 400);
        } else {
            setActiveDetails(null);
        }
    };

    // Handle continue button
    const handleContinue = () => {
        if (!selectedAlignment) {
            alert("Please select an alignment for your character.");
            return;
        }
        
        // Update character data with selected alignment
        updateCharacterData({
            alignment: selectedAlignment,
            alignmentName: alignments.find(a => a.id === selectedAlignment)?.name || "Unknown Alignment"
        });
        
        // Move to next step
        nextStep();
    };

    return (
        <div className="step10-outer-container">
            {/* Title */}
            <h2 className="step10-title">Choose Your Alignment</h2>
            
            {/* Alignment Explanation */}
            <div className="alignment-explanation">
                <h3>What is Alignment?</h3>
                <p>
                    Alignment reflects your character's basic moral and ethical attitudes. It combines two factors:
                    one identifies where your character falls between law and chaos, the other between good and evil.
                    Choose the alignment that best represents how your character will behave during adventures.
                </p>
            </div>
            
            {/* Alignment Grid */}
            <div className="alignment-grid-container">
                {alignments.map((alignment) => (
                    <div 
                        key={alignment.id}
                        className={`alignment-card ${alignment.axis} ${alignment.morality} ${selectedAlignment === alignment.id ? 'selected' : ''}`}
                        onClick={() => handleSelectAlignment(alignment.id)}
                    >
                        <h3 className="alignment-name">{alignment.name}</h3>
                        <p className="alignment-description">{alignment.description}</p>
                        <p className="alignment-example">Example: {alignment.examples}</p>
                        
                        <button 
                            className="alignment-details-button"
                            onClick={(e) => handleShowDetails(alignment, e)}
                        >
                            More Details
                        </button>
                        
                        <div className="selected-indicator">
                            <i className="bi bi-check-circle-fill"></i>
                        </div>
                    </div>
                ))}
            </div>
            
            {/* Alignment Details Modal */}
            {activeDetails && (
                <div 
                    className="alignment-details-overlay" 
                    ref={detailsModalRef} 
                    onClick={handleCloseDetails}
                >
                    <div className="alignment-details-modal" onClick={(e) => e.stopPropagation()}>
                        <button className="close-button" onClick={handleCloseDetails}>×</button>
                        
                        <div className="alignment-details-header">
                            <h3 className="alignment-details-title">{activeDetails.name}</h3>
                        </div>
                        
                        <div className="alignment-details-content">
                            <p className="alignment-details-description">{activeDetails.fullDescription}</p>
                            
                            {/* Typical behaviors section */}
                            <div className="alignment-details-section">
                                <h4>Typical Behaviors</h4>
                                <p>{activeDetails.details}</p>
                            </div>
                            
                            {/* Examples section */}
                            <div className="alignment-details-section">
                                <h4>Example</h4>
                                <div className="alignment-details-example">
                                    <p className="example-text">{activeDetails.examples}</p>
                                </div>
                            </div>
                            
                            {/* Character types section */}
                            <div className="alignment-details-section">
                                <h4>Common Character Types</h4>
                                <div className="characters-list">
                                    {activeDetails.characters.map((character, index) => (
                                        <span className="character-tag" key={index}>{character}</span>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
            
            {/* Navigation Buttons */}
            <div className="step10-navigation">
                <button className="back-button" onClick={prevStep}>
                    <i className="bi bi-arrow-left"></i> Back to Equipment
                </button>
                
                <button 
                    className={`continue-button ${selectedAlignment ? 'active' : ''}`}
                    onClick={handleContinue}
                    disabled={!selectedAlignment}
                >
                    Continue to Finish <i className="bi bi-arrow-right"></i>
                </button>
            </div>
        </div>
    );
}

export default Step10_AlignmentSelector;