// File: frontend/src/components/steps/Step5_AbilityScores.jsx

import React, { useState, useEffect, useCallback, useRef } from 'react';
import './Step5_AbilityScores.css';

// Helper function to calculate ability modifier
const calculateModifier = (score) => {
  return Math.floor((score - 10) / 2);
};

// Helper function to get modifier text with + or - sign
const getModifierText = (score) => {
  const modifier = calculateModifier(score);
  return modifier >= 0 ? `+${modifier}` : `${modifier}`;
};

// Helper function to get modifier class based on value
const getModifierClass = (score) => {
  const modifier = calculateModifier(score);
  if (modifier > 0) return "positive";
  if (modifier < 0) return "negative";
  return "zero";
};

// Helper function to get score class based on modifier value
const getScoreClass = (score) => {
  const modifier = calculateModifier(score);
  if (modifier > 0) return "positive-modifier";
  if (modifier < 0) return "negative-modifier";
  return "zero-modifier";
};

// Standard array values
const STANDARD_ARRAY = [15, 14, 13, 12, 10, 8];

// Ability descriptions
const ABILITY_DESCRIPTIONS = {
  strength: "Physical power, athletic training, and raw might",
  dexterity: "Agility, reflexes, balance, and hand-eye coordination",
  constitution: "Health, stamina, vital force, and physical resilience",
  intelligence: "Mental acuity, information recall, analytical skill",
  wisdom: "Awareness, intuition, insight, and perceptiveness",
  charisma: "Force of personality, persuasiveness, leadership, and confidence"
};

const [diceAnimations, setDiceAnimations] = useState([]);
const [showDiceValues, setShowDiceValues] = useState(false);
const diceAnimationRef = useRef(null);

function Step5_AbilityScores({ characterData, updateCharacterData, nextStep, prevStep }) {
  // State for the selected method
  const [selectedMethod, setSelectedMethod] = useState(null);
  
  // State for ability scores
  const [abilityScores, setAbilityScores] = useState({
    strength: 8,
    dexterity: 8,
    constitution: 8,
    intelligence: 8, 
    wisdom: 8,
    charisma: 8
  });
  
  // State for point buy
  const [pointsRemaining, setPointsRemaining] = useState(27);
  
  // State for dice rolls
  const [diceRolls, setDiceRolls] = useState(Array(6).fill([]).map(() => Array(4).fill(0)));
  const [rollResults, setRollResults] = useState([]);
  const [selectedRolls, setSelectedRolls] = useState([]);
  const [isRolling, setIsRolling] = useState(false);
  
  // State for standard array
  const [standardArray, setStandardArray] = useState([...STANDARD_ARRAY]);
  const [usedArrayValues, setUsedArrayValues] = useState([]);
  const [draggedValue, setDraggedValue] = useState(null);
  
  // State for validation
  const [validationError, setValidationError] = useState('');
  const [canContinue, setCanContinue] = useState(false);
  
  // Refs
  const validationAlertRef = useRef(null);
  
  // Racial bonuses from characterData
  const racialBonuses = useRef({});
  
  // Effect to extract racial bonuses from character data
  useEffect(() => {
    const bonuses = {};
    
    if (characterData.raceId && characterData.races) {
      // Find the race in the data
      const race = characterData.races.find(r => r.id === characterData.raceId);
      
      if (race && race.abilityScoreAdjustments) {
        // Add race bonuses
        Object.entries(race.abilityScoreAdjustments).forEach(([ability, bonus]) => {
          bonuses[ability] = (bonuses[ability] || 0) + bonus;
        });
      }
      
      // Add subrace bonuses if applicable
      if (characterData.subraceId && race.subraces) {
        const subrace = race.subraces.find(sr => sr.id === characterData.subraceId);
        
        if (subrace && subrace.abilityScoreAdjustments) {
          Object.entries(subrace.abilityScoreAdjustments).forEach(([ability, bonus]) => {
            bonuses[ability] = (bonuses[ability] || 0) + bonus;
          });
        }
      }
    }
    
    racialBonuses.current = bonuses;
  }, [characterData]);
  
  // Calculate total ability scores including racial bonuses
  const calculateTotalScores = () => {
    const totalScores = {};
    
    Object.entries(abilityScores).forEach(([ability, score]) => {
      const racialBonus = racialBonuses.current[ability] || 0;
      totalScores[ability] = score + racialBonus;
    });
    
    return totalScores;
  };
  
  // Set validation error with animation
  const setError = (message) => {
    setValidationError(message);
    
    if (validationAlertRef.current) {
      validationAlertRef.current.classList.add('visible');
      validationAlertRef.current.classList.add('shake');
      
      setTimeout(() => {
        if (validationAlertRef.current) {
          validationAlertRef.current.classList.remove('shake');
        }
      }, 500);
    }
  };
  
  // Clear validation error
  const clearError = () => {
    setValidationError('');
    if (validationAlertRef.current) {
      validationAlertRef.current.classList.remove('visible');
    }
  };
  
  // Handler for method selection
  const handleMethodSelect = (method) => {
    setSelectedMethod(method);
    clearError();
    
    // Reset ability scores
    setAbilityScores({
      strength: 8,
      dexterity: 8,
      constitution: 8,
      intelligence: 8,
      wisdom: 8,
      charisma: 8
    });
    
    // Reset method-specific states
    if (method === 'pointBuy') {
      setPointsRemaining(27);
    } else if (method === 'diceRoll') {
      setDiceRolls(Array(6).fill([]).map(() => Array(4).fill(0)));
      setRollResults([]);
      setSelectedRolls([]);
    } else if (method === 'standardArray') {
      setStandardArray([...STANDARD_ARRAY]);
      setUsedArrayValues([]);
    }
  };
  
  // Handler for point buy method
  const handlePointBuy = (ability, change) => {
    // Get current score
    const currentScore = abilityScores[ability];
    const newScore = currentScore + change;
    
    // Check bounds (8-15)
    if (newScore < 8 || newScore > 15) return;
    
    // Calculate point cost or refund
    let pointCost = 0;
    
    if (change > 0) {
      // Increasing score
      if (currentScore >= 13) {
        // Costs 2 points per increase after 13
        pointCost = 2;
      } else {
        // Costs 1 point normally
        pointCost = 1;
      }
      
      // Check if we have enough points
      if (pointsRemaining < pointCost) {
        setError('Not enough points remaining!');
        return;
      }
    } else {
      // Decreasing score, refund points
      if (currentScore > 13) {
        // Refund 2 points per decrease
        pointCost = -2;
      } else {
        // Refund 1 point normally
        pointCost = -1;
      }
    }
    
    // Update score and points
    setAbilityScores(prev => ({
      ...prev,
      [ability]: newScore
    }));
    
    setPointsRemaining(prev => prev - pointCost);
    clearError();
  };
  
  // Dice rolling
  const rollDice = () => {
    if (isRolling) return;
    
    setIsRolling(true);
    clearError();
    setShowDiceValues(false);
    
    // Stop any existing animation
    if (diceAnimationRef.current) {
      clearTimeout(diceAnimationRef.current);
    }
    
    // Generate 6 sets of 4d6 rolls
    const newRolls = [];
    
    for (let i = 0; i < 6; i++) {
      const dice = [];
      for (let j = 0; j < 4; j++) {
        dice.push(Math.floor(Math.random() * 6) + 1); // 1-6
      }
      newRolls.push(dice);
    }
    
    // Prepare animation sequence
    const animationSteps = 15; // Number of frames in animation
    const diceAnimationFrames = [];
    
    // Create random values for each animation frame
    for (let step = 0; step < animationSteps; step++) {
      const frameData = [];
      
      for (let i = 0; i < 6; i++) {
        const diceSet = [];
        for (let j = 0; j < 4; j++) {
          // Gradually converge to final value
          const convergenceFactor = step / animationSteps;
          if (Math.random() > convergenceFactor) {
            diceSet.push(Math.floor(Math.random() * 6) + 1);
          } else {
            diceSet.push(newRolls[i][j]);
          }
        }
        frameData.push(diceSet);
      }
      
      diceAnimationFrames.push(frameData);
    }
    
    // Add the final values
    diceAnimationFrames.push([...newRolls]);
    
    // Set initial animation frame
    setDiceRolls(diceAnimationFrames[0]);
    setDiceAnimations(diceAnimationFrames);
    
    // Start animation
    let currentFrame = 0;
    const animationInterval = 80; // ms between frames
    
    const runAnimation = () => {
      currentFrame++;
      
      if (currentFrame < diceAnimationFrames.length) {
        setDiceRolls(diceAnimationFrames[currentFrame]);
        diceAnimationRef.current = setTimeout(runAnimation, animationInterval);
      } else {
        // Animation complete
        finishRolling(newRolls);
      }
    };
    
    // Start the animation
    diceAnimationRef.current = setTimeout(runAnimation, animationInterval);
  };
  
  // Animate dice rolls visually
  const animateDiceRolls = (finalRolls) => {
    // Start with random values
    setDiceRolls(Array(6).fill([]).map(() => Array(4).fill(0).map(() => Math.floor(Math.random() * 6) + 1)));
    
    // Animate changing values
    let iterations = 0;
    const maxIterations = 10;
    const interval = 100; // ms
    
    const animation = setInterval(() => {
      iterations++;
      
      if (iterations < maxIterations) {
        // Still animating - show random values
        setDiceRolls(prev => prev.map((set, i) => 
          set.map((_, j) => {
            // Gradually converge to final value
            const convergence = iterations / maxIterations;
            if (Math.random() > convergence) {
              return Math.floor(Math.random() * 6) + 1;
            } else {
              return finalRolls[i][j];
            }
          })
        ));
      } else {
        // Animation complete
        clearInterval(animation);
        setDiceRolls(finalRolls);
        
        // Calculate results (drop lowest die from each set)
        const results = finalRolls.map(diceSet => {
          const sorted = [...diceSet].sort((a, b) => a - b);
          const sum = sorted.slice(1).reduce((a, b) => a + b, 0);
          return sum;
        });
        
        setRollResults(results);
        setSelectedRolls([]);
        setIsRolling(false);
      }
    }, interval);
  };

  const finishRolling = (finalRolls) => {
    // Calculate results (drop lowest die from each set)
    const results = finalRolls.map(diceSet => {
      const sorted = [...diceSet].sort((a, b) => a - b);
      const sum = sorted.slice(1).reduce((a, b) => a + b, 0);
      return sum;
    });
    
    setDiceRolls(finalRolls);
    setRollResults(results);
    setSelectedRolls([]);
    setIsRolling(false);
    setShowDiceValues(true);
    
    // Clear animation reference
    diceAnimationRef.current = null;
  };
  
  // Add cleanup effect for animations
  useEffect(() => {
    return () => {
      // Clear any ongoing animations when component unmounts
      if (diceAnimationRef.current) {
        clearTimeout(diceAnimationRef.current);
      }
    };
  }, []);
  
  
  // Handler for selecting a roll and assigning to ability
  const handleSelectRoll = (rollIndex, ability) => {
    // Check if roll is already selected
    if (selectedRolls.includes(rollIndex)) {
      return;
    }
    
    // Create a flashy animation for the selected roll
    const diceResultElement = document.querySelector(`.dice-set:nth-child(${rollIndex + 1}) .dice-result`);
    if (diceResultElement) {
      diceResultElement.classList.add('highlighted');
    }
    
    // Update ability score with a slight delay to make it feel responsive
    setTimeout(() => {
      setAbilityScores(prev => ({
        ...prev,
        [ability]: rollResults[rollIndex]
      }));
      
      // Mark roll as used
      setSelectedRolls(prev => [...prev, rollIndex]);
      
      clearError();
    }, 200);
  };
  
  // Handlers for standard array drag-and-drop
  const handleDragStart = (value) => {
    // Check if value is already used
    if (usedArrayValues.includes(value)) {
      return;
    }
    
    setDraggedValue(value);
  };
  
  const handleDragOver = (e, ability) => {
    // Prevent default to allow drop
    e.preventDefault();
    
    // Add drop target styling
    e.currentTarget.classList.add('drop-target');
  };
  
  const handleDragLeave = (e) => {
    // Remove drop target styling
    e.currentTarget.classList.remove('drop-target');
  };
  
  const handleDrop = (e, ability) => {
    e.preventDefault();
    
    // Remove drop target styling
    e.currentTarget.classList.remove('drop-target');
    
    // Check if we have a dragged value
    if (draggedValue === null) return;
    
    // Update ability score
    setAbilityScores(prev => ({
      ...prev,
      [ability]: draggedValue
    }));
    
    // Mark value as used
    setUsedArrayValues(prev => [...prev, draggedValue]);
    
    // Clear dragged value
    setDraggedValue(null);
    
    clearError();
  };
  
  // Recommended ability scores based on class
  const getRecommendedScores = () => {
    const classPriorities = {
      barbarian: ['strength', 'constitution', 'dexterity', 'charisma', 'wisdom', 'intelligence'],
      bard: ['charisma', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'strength'],
      cleric: ['wisdom', 'constitution', 'strength', 'charisma', 'intelligence', 'dexterity'],
      druid: ['wisdom', 'constitution', 'dexterity', 'intelligence', 'charisma', 'strength'],
      fighter: ['strength', 'constitution', 'dexterity', 'wisdom', 'charisma', 'intelligence'], // STR fighter
      monk: ['dexterity', 'wisdom', 'constitution', 'strength', 'charisma', 'intelligence'],
      paladin: ['strength', 'charisma', 'constitution', 'wisdom', 'intelligence', 'dexterity'],
      ranger: ['dexterity', 'wisdom', 'constitution', 'intelligence', 'strength', 'charisma'],
      rogue: ['dexterity', 'constitution', 'charisma', 'intelligence', 'wisdom', 'strength'],
      sorcerer: ['charisma', 'constitution', 'dexterity', 'intelligence', 'wisdom', 'strength'],
      warlock: ['charisma', 'constitution', 'dexterity', 'wisdom', 'intelligence', 'strength'],
      wizard: ['intelligence', 'constitution', 'dexterity', 'wisdom', 'charisma', 'strength']
    };
    
    // Get priority list for the character's class
    const priorities = classPriorities[characterData.classId] || 
      ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma'];
    
    // Assign scores based on method
    if (selectedMethod === 'pointBuy') {
      // Point buy recommended distribution
      const recommendedScores = {
        strength: 8,
        dexterity: 8,
        constitution: 8,
        intelligence: 8,
        wisdom: 8,
        charisma: 8
      };
      
      // Prioritize abilities
      let remainingPoints = 27;
      const targetScores = [15, 14, 13, 12, 10, 8];
      
      // Assign target scores based on priorities
      for (let i = 0; i < priorities.length; i++) {
        if (i < targetScores.length) {
          const ability = priorities[i];
          const targetScore = targetScores[i];
          const currentScore = recommendedScores[ability];
          const pointsNeeded = getPointCost(currentScore, targetScore);
          
          if (remainingPoints >= pointsNeeded) {
            recommendedScores[ability] = targetScore;
            remainingPoints -= pointsNeeded;
          }
        }
      }
      
      return recommendedScores;
    } 
    else if (selectedMethod === 'standardArray') {
      // Standard array assignment
      const recommendedScores = {
        strength: 8,
        dexterity: 8,
        constitution: 8,
        intelligence: 8,
        wisdom: 8,
        charisma: 8
      };
      
      // Assign array values based on priorities
      for (let i = 0; i < Math.min(priorities.length, STANDARD_ARRAY.length); i++) {
        recommendedScores[priorities[i]] = STANDARD_ARRAY[i];
      }
      
      return recommendedScores;
    }
    else if (selectedMethod === 'diceRoll' && rollResults.length === 6) {
      // Dice roll assignment - sort rolls from highest to lowest
      const sortedRolls = [...rollResults].sort((a, b) => b - a);
      const recommendedScores = {
        strength: 8,
        dexterity: 8,
        constitution: 8,
        intelligence: 8,
        wisdom: 8,
        charisma: 8
      };
      
      // Assign rolls based on priorities
      for (let i = 0; i < Math.min(priorities.length, sortedRolls.length); i++) {
        recommendedScores[priorities[i]] = sortedRolls[i];
      }
      
      return recommendedScores;
    }
    
    // Default return
    return {
      strength: 8,
      dexterity: 8,
      constitution: 8,
      intelligence: 8,
      wisdom: 8,
      charisma: 8
    };
  };
  
  // Apply recommended scores
  const applyRecommendedScores = () => {
    const recommended = getRecommendedScores();
    
    // Apply to ability scores
    setAbilityScores(recommended);
    
    // Update method-specific state
    if (selectedMethod === 'pointBuy') {
      // Calculate points used
      const pointsUsed = Object.values(recommended).reduce((total, score) => {
        return total + getPointCost(8, score);
      }, 0);
      
      setPointsRemaining(27 - pointsUsed);
    }
    else if (selectedMethod === 'standardArray') {
      // Mark all standard array values as used
      setUsedArrayValues([...STANDARD_ARRAY]);
    }
    else if (selectedMethod === 'diceRoll') {
      // Mark all rolls as selected
      setSelectedRolls([0, 1, 2, 3, 4, 5]);
    }
    
    clearError();
  };
  
  // Helper for point cost calculation
  const getPointCost = (startScore, endScore) => {
    let cost = 0;
    
    for (let i = startScore; i < endScore; i++) {
      if (i >= 13) {
        cost += 2;
      } else {
        cost += 1;
      }
    }
    
    return cost;
  };
  
  // Validate ability scores before continuing
  const validateScores = () => {
    // Check if method is selected
    if (!selectedMethod) {
      setError('Please select a method for determining ability scores.');
      return false;
    }
    
    // Method-specific validation
    if (selectedMethod === 'pointBuy') {
      // Check if all points are spent
      if (pointsRemaining > 0) {
        setError(`You still have ${pointsRemaining} points to spend.`);
        return false;
      }
    }
    else if (selectedMethod === 'diceRoll') {
      // Check if all rolls are assigned
      if (selectedRolls.length < 6) {
        setError('Please assign all rolled values to abilities.');
        return false;
      }
    }
    else if (selectedMethod === 'standardArray') {
      // Check if all array values are used
      if (usedArrayValues.length < 6) {
        setError('Please assign all standard array values to abilities.');
        return false;
      }
    }
    
    return true;
  };
  
  // Handle continue button
  const handleContinue = () => {
    if (!validateScores()) {
      return;
    }
    
    // Calculate final scores with racial bonuses
    const finalScores = calculateTotalScores();
    
    // Update character data
    updateCharacterData({
      abilityScores: abilityScores,
      finalAbilityScores: finalScores,
      scoreMethod: selectedMethod
    });
    
    // Move to next step
    nextStep();
  };
  
  // Check if we can continue
  useEffect(() => {
    if (selectedMethod === 'pointBuy' && pointsRemaining === 0) {
      setCanContinue(true);
    }
    else if (selectedMethod === 'diceRoll' && selectedRolls.length === 6) {
      setCanContinue(true);
    }
    else if (selectedMethod === 'standardArray' && usedArrayValues.length === 6) {
      setCanContinue(true);
    }
    else {
      setCanContinue(false);
    }
  }, [selectedMethod, pointsRemaining, selectedRolls, usedArrayValues]);
  
  // Render ability card
  const renderAbilityCard = (ability) => {
    const abilityName = ability.charAt(0).toUpperCase() + ability.slice(1);
    const score = abilityScores[ability];
    const racialBonus = racialBonuses.current[ability] || 0;
    const totalScore = score + racialBonus;
    const modifier = calculateModifier(totalScore);
    const modifierText = getModifierText(totalScore);
    
    return (
      <div 
        className="ability-card"
        onDragOver={selectedMethod === 'standardArray' ? (e) => handleDragOver(e, ability) : null}
        onDragLeave={selectedMethod === 'standardArray' ? handleDragLeave : null}
        onDrop={selectedMethod === 'standardArray' ? (e) => handleDrop(e, ability) : null}
      >
        <div className="ability-name">{abilityName}</div>
        <div className="ability-description">{ABILITY_DESCRIPTIONS[ability]}</div>
        
        <div className="ability-score-display">
          <div className="ability-controls">
            {selectedMethod === 'pointBuy' && (
              <button 
                className="ability-btn"
                onClick={() => handlePointBuy(ability, -1)}
                disabled={score <= 8}
              >
                <i className="bi bi-dash"></i>
              </button>
            )}
            
            <div className={`ability-score ${getScoreClass(totalScore)}`}>
              {score}
              <span className={`ability-modifier ${getModifierClass(totalScore)}`}>
                {modifierText}
              </span>
            </div>
            
            {selectedMethod === 'pointBuy' && (
              <button 
                className="ability-btn"
                onClick={() => handlePointBuy(ability, 1)}
                disabled={score >= 15 || pointsRemaining < (score >= 13 ? 2 : 1)}
              >
                <i className="bi bi-plus"></i>
              </button>
            )}
          </div>
        </div>
        
        {racialBonus > 0 && (
          <div className="racial-bonus">+{racialBonus} Racial Bonus</div>
        )}
        
        {selectedMethod === 'diceRoll' && rollResults.length > 0 && (
          <div className="die-selection">
            <select 
              className="die-select form-select bg-dark text-light mt-2"
              onChange={(e) => handleSelectRoll(parseInt(e.target.value), ability)}
              value=""
            >
              <option value="" disabled>Select a roll</option>
              {rollResults.map((roll, idx) => (
                !selectedRolls.includes(idx) && 
                <option key={idx} value={idx}>
                  Roll {idx + 1}: {roll}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>
    );
  };
  
  return (
    <div className="step5-outer-container">
      {/* Title */}
      <h2 className="step5-title">Ability Scores</h2>
      
      {/* Validation alert */}
      <div 
        ref={validationAlertRef}
        className={`validation-alert ${validationError ? 'visible' : ''}`}
      >
        {validationError}
      </div>
      
      {/* Method selection */}
      <div className="method-selection-container">
        {/* Point Buy Method */}
        <div 
          className={`method-card ${selectedMethod === 'pointBuy' ? 'selected' : ''}`}
          onClick={() => handleMethodSelect('pointBuy')}
        >
          <div className="method-icon">
            <i className="bi bi-calculator"></i>
          </div>
          <div className="method-name">Point Buy</div>
          <div className="method-description">
            Spend 27 points to customize your ability scores between 8 and 15.
          </div>
        </div>
        
        {/* Dice Roll Method */}
        <div 
          className={`method-card ${selectedMethod === 'diceRoll' ? 'selected' : ''}`}
          onClick={() => handleMethodSelect('diceRoll')}
        >
          <div className="method-icon">
            <i className="bi bi-dice-6"></i>
          </div>
          <div className="method-name">Dice Roll</div>
          <div className="method-description">
            Roll 4d6 six times, dropping the lowest die from each roll.
          </div>
        </div>
        
        {/* Standard Array Method */}
        <div 
          className={`method-card ${selectedMethod === 'standardArray' ? 'selected' : ''}`}
          onClick={() => handleMethodSelect('standardArray')}
        >
          <div className="method-icon">
            <i className="bi bi-grid-3x2"></i>
          </div>
          <div className="method-name">Standard Array</div>
          <div className="method-description">
            Use the standard array of 15, 14, 13, 12, 10, 8 for your ability scores.
          </div>
        </div>
      </div>
      
      {/* Method-specific UI */}
      {selectedMethod && (
        <div className="ability-scores-container">
          <div className="ability-scores-header">
            {/* Header content based on method */}
            {selectedMethod === 'pointBuy' && (
              <div className="points-remaining">
                Points Remaining: <span>{pointsRemaining}</span>
              </div>
            )}
            
            {/* Recommendation button */}
            <div className="recommendation-container">
              <button 
                className="recommend-btn"
                onClick={applyRecommendedScores}
              >
                <i className="bi bi-magic"></i> Recommended for {characterData.className}
              </button>
            </div>
          </div>
          
          {/* Method explanation */}
          {selectedMethod === 'pointBuy' && (
            <div className="method-explanation">
              <p><strong>Point Buy Rules:</strong> All abilities start at 8. Each increase costs 1 point up to 13, and 2 points from 14 to 15. The maximum score before racial bonuses is 15.</p>
            </div>
          )}
          
          {selectedMethod === 'diceRoll' && !rollResults.length && (
            <div className="roll-button-container">
                <button className="roll-button" onClick={rollDice} disabled={isRolling}>
                <i className="bi bi-dice-6"></i> Roll 4d6 (drop lowest) × 6
                </button>
            </div>
            )}
          
          {selectedMethod === 'diceRoll' && (diceRolls.length > 0 || isRolling) && (
            <div className="dice-container">
                {diceRolls.map((diceSet, setIndex) => (
                <div key={setIndex} className="dice-set">
                    <div className="dice-row">
                    {diceSet.map((value, dieIndex) => (
                        <div 
                        key={`${setIndex}-${dieIndex}`} 
                        className={`die ${isRolling ? 'rolling' : ''} ${selectedRolls.includes(setIndex) ? 'selected' : ''}`}
                        >
                        <div className="die-inner">
                            <div className="die-face">
                            {showDiceValues ? (
                                value
                            ) : (
                                <div className="rolling-dots">
                                {Array.from({ length: value }).map((_, i) => (
                                    <div key={i} className="die-dot"></div>
                                ))}
                                </div>
                            )}
                            </div>
                        </div>
                        </div>
                    ))}
                    </div>
                    {rollResults.length > 0 && (
                    <div className={`dice-result ${selectedRolls.includes(setIndex) ? 'highlighted' : ''}`}>
                        Total: {rollResults[setIndex]}
                    </div>
                    )}
                </div>
                ))}
            </div>
            )}
          
          {selectedMethod === 'diceRoll' && rollResults.length > 0 && (
            <div className="roll-instruction">
                {selectedRolls.length < 6 ? (
                "Assign each result to an ability using the dropdowns below."
                ) : (
                "All rolls have been assigned to abilities."
                )}
            </div>
            )}
          
          {selectedMethod === 'standardArray' && (
            <div className="array-values-container">
              {standardArray.map((value, idx) => (
                <div
                  key={idx}
                  className={`array-value ${usedArrayValues.includes(value) ? 'used' : ''}`}
                  draggable={!usedArrayValues.includes(value)}
                  onDragStart={() => handleDragStart(value)}
                >
                  {value}
                </div>
              ))}
            </div>
          )}
          
          {selectedMethod === 'standardArray' && (
            <div className="drag-instruction">
              Drag and drop the values onto the ability cards below.
            </div>
          )}
          
          {/* Ability cards grid */}
          <div className="abilities-grid">
            {renderAbilityCard('strength')}
            {renderAbilityCard('dexterity')}
            {renderAbilityCard('constitution')}
            {renderAbilityCard('intelligence')}
            {renderAbilityCard('wisdom')}
            {renderAbilityCard('charisma')}
          </div>
        </div>
      )}
      
      {/* Navigation Buttons */}
      <div className="step5-navigation">
        <button className="back-button" onClick={prevStep}>
          <i className="bi bi-arrow-left"></i> Back to Character Info
        </button>
        
        <button 
          className={`continue-button ${canContinue ? 'active' : ''}`}
          onClick={handleContinue}
          disabled={!canContinue}
        >
          Continue to Skills <i className="bi bi-arrow-right"></i>
        </button>
      </div>
    </div>
  );
}

export default Step5_AbilityScores;