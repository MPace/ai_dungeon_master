/**
 * Character Creation Module for AI Dungeon Master
 */

// Character data object
let characterData = {
    name: '',
    race: '',
    class: '',
    background: '',
    level: 1,
    abilities: {
        strength: 10,
        dexterity: 10,
        constitution: 10,
        intelligence: 10,
        wisdom: 10,
        charisma: 10
    },
    skills: [],
    equipment: [],
    spells: [],
    features: [],
    description: ''
};

// Updated Race data with sub-races
const raceData = {
    human: {
        name: 'Human',
        description: 'Versatile and ambitious, humans are the most common race in most worlds.',
        abilityScoreIncrease: { all: 1 },
        traits: ['Versatile: +1 to all ability scores'],
        hasSubraces: false,
        subraces: []
    },
    elf: {
        name: 'Elf',
        description: 'Elves are a magical people of otherworldly grace, living in the world but not entirely part of it.',
        abilityScoreIncrease: { dexterity: 2 },
        traits: ['Darkvision', 'Keen Senses', 'Fey Ancestry', 'Trance'],
        hasSubraces: true,
        subraces: [
            {
                id: 'high-elf',
                name: 'High Elf',
                description: 'High elves have a keen mind and a mastery of at least basic magic.',
                abilityScoreIncrease: { intelligence: 1 },
                traits: ['Cantrip', 'Extra Language']
            },
            {
                id: 'wood-elf',
                name: 'Wood Elf',
                description: 'Wood elves have keen senses and intuition, and their fleet feet carry them quickly through the forest.',
                abilityScoreIncrease: { wisdom: 1 },
                traits: ['Fleet of Foot', 'Mask of the Wild']
            },
            {
                id: 'dark-elf',
                name: 'Dark Elf (Drow)',
                description: 'Dark elves dwell deep in the Underdark, a complex network of caves and tunnels beneath the surface.',
                abilityScoreIncrease: { charisma: 1 },
                traits: ['Superior Darkvision', 'Sunlight Sensitivity', 'Drow Magic']
            }
        ]
    },
    dwarf: {
        name: 'Dwarf',
        description: 'Bold and hardy, dwarves are known as skilled warriors, miners, and workers of stone and metal.',
        abilityScoreIncrease: { constitution: 2 },
        traits: ['Darkvision', 'Dwarven Resilience', 'Stonecunning'],
        hasSubraces: true,
        subraces: [
            {
                id: 'hill-dwarf',
                name: 'Hill Dwarf',
                description: 'Hill dwarves have keen senses, deep intuition, and remarkable resilience.',
                abilityScoreIncrease: { wisdom: 1 },
                traits: ['Dwarven Toughness']
            },
            {
                id: 'mountain-dwarf',
                name: 'Mountain Dwarf',
                description: 'Mountain dwarves are strong and hardy, accustomed to a difficult life in rugged terrain.',
                abilityScoreIncrease: { strength: 2 },
                traits: ['Dwarven Armor Training']
            }
        ]
    },
    halfling: {
        name: 'Halfling',
        description: 'Small and practical, halflings survive in a world full of larger creatures by avoiding notice or, barring that, avoiding offense.',
        abilityScoreIncrease: { dexterity: 2 },
        traits: ['Lucky', 'Brave', 'Halfling Nimbleness'],
        hasSubraces: true,
        subraces: [
            {
                id: 'lightfoot',
                name: 'Lightfoot',
                description: 'Lightfoot halflings are more nimble and stealthy than their kin, but they are also more prone to wanderlust.',
                abilityScoreIncrease: { charisma: 1 },
                traits: ['Naturally Stealthy']
            },
            {
                id: 'stout',
                name: 'Stout',
                description: 'Stout halflings are hardier than average and have some resistance to poison.',
                abilityScoreIncrease: { constitution: 1 },
                traits: ['Stout Resilience']
            }
        ]
    },
    dragonborn: {
        name: 'Dragonborn',
        description: 'Dragonborn look very much like dragons standing erect in humanoid form, though they lack wings or a tail.',
        abilityScoreIncrease: { strength: 2, charisma: 1 },
        traits: ['Draconic Ancestry', 'Breath Weapon', 'Damage Resistance'],
        hasSubraces: false,
        subraces: []
    }
};

// Class data
const classData = {
    fighter: {
        name: 'Fighter',
        description: 'A master of martial combat, skilled with a variety of weapons and armor.',
        hitDie: 'd10',
        primaryAbility: 'Strength or Dexterity',
        savingThrows: ['Strength', 'Constitution'],
        features: ['Fighting Style', 'Second Wind']
    },
    wizard: {
        name: 'Wizard',
        description: 'A scholarly magic-user capable of manipulating the structures of reality.',
        hitDie: 'd6',
        primaryAbility: 'Intelligence',
        savingThrows: ['Intelligence', 'Wisdom'],
        features: ['Spellcasting', 'Arcane Recovery']
    },
    cleric: {
        name: 'Cleric',
        description: 'A priestly champion who wields divine magic in service of a higher power.',
        hitDie: 'd8',
        primaryAbility: 'Wisdom',
        savingThrows: ['Wisdom', 'Charisma'],
        features: ['Spellcasting', 'Divine Domain']
    },
    rogue: {
        name: 'Rogue',
        description: 'A scoundrel who uses stealth and trickery to overcome obstacles and enemies.',
        hitDie: 'd8',
        primaryAbility: 'Dexterity',
        savingThrows: ['Dexterity', 'Intelligence'],
        features: ['Expertise', 'Sneak Attack', 'Thieves\' Cant']
    },
    bard: {
        name: 'Bard',
        description: 'An inspiring magician whose power echoes the music of creation.',
        hitDie: 'd8',
        primaryAbility: 'Charisma',
        savingThrows: ['Dexterity', 'Charisma'],
        features: ['Spellcasting', 'Bardic Inspiration']
    }
};

// Background data
const backgroundData = {
    acolyte: {
        name: 'Acolyte',
        description: 'You have spent your life in service to a temple, learning sacred rites and providing sacrifices to your god.',
        skillProficiencies: ['Insight', 'Religion'],
        feature: 'Shelter of the Faithful'
    },
    criminal: {
        name: 'Criminal',
        description: 'You have a history of breaking the law and survive by leveraging your connections to the criminal underworld.',
        skillProficiencies: ['Deception', 'Stealth'],
        feature: 'Criminal Contact'
    },
    noble: {
        name: 'Noble',
        description: 'You understand wealth, power, and privilege. Your family name carries weight in high society.',
        skillProficiencies: ['History', 'Persuasion'],
        feature: 'Position of Privilege'
    },
    soldier: {
        name: 'Soldier',
        description: 'You have been trained in warfare and know what it means to fight in a military force.',
        skillProficiencies: ['Athletics', 'Intimidation'],
        feature: 'Military Rank'
    },
    sage: {
        name: 'Sage',
        description: 'You have spent years learning lore and studying ancient texts and historical events.',
        skillProficiencies: ['Arcana', 'History'],
        feature: 'Researcher'
    }
};

// Skills object (global to prevent scope issues)
const skills = {
    acrobatics: { name: 'Acrobatics', ability: 'dexterity' },
    animalHandling: { name: 'Animal Handling', ability: 'wisdom' },
    arcana: { name: 'Arcana', ability: 'intelligence' },
    athletics: { name: 'Athletics', ability: 'strength' },
    deception: { name: 'Deception', ability: 'charisma' },
    history: { name: 'History', ability: 'intelligence' },
    insight: { name: 'Insight', ability: 'wisdom' },
    intimidation: { name: 'Intimidation', ability: 'charisma' },
    investigation: { name: 'Investigation', ability: 'intelligence' },
    medicine: { name: 'Medicine', ability: 'wisdom' },
    nature: { name: 'Nature', ability: 'intelligence' },
    perception: { name: 'Perception', ability: 'wisdom' },
    performance: { name: 'Performance', ability: 'charisma' },
    persuasion: { name: 'Persuasion', ability: 'charisma' },
    religion: { name: 'Religion', ability: 'intelligence' },
    sleightOfHand: { name: 'Sleight of Hand', ability: 'dexterity' },
    stealth: { name: 'Stealth', ability: 'dexterity' },
    survival: { name: 'Survival', ability: 'wisdom' }
};

// Define class skills object
const classSkills = {
    fighter: ['acrobatics', 'animalHandling', 'athletics', 'history', 'insight', 'intimidation', 'perception', 'survival'],
    wizard: ['arcana', 'history', 'insight', 'investigation', 'medicine', 'religion'],
    cleric: ['history', 'insight', 'medicine', 'persuasion', 'religion'],
    rogue: ['acrobatics', 'athletics', 'deception', 'insight', 'intimidation', 'investigation', 'perception', 'performance', 'persuasion', 'sleightOfHand', 'stealth'],
    bard: ['acrobatics', 'animalHandling', 'arcana', 'athletics', 'deception', 'history', 'insight', 'intimidation', 'investigation', 'medicine', 'nature', 'perception', 'performance', 'persuasion', 'religion', 'sleightOfHand', 'stealth', 'survival']
};


// Class Features Data Structure
const classFeatures = {
    fighter: {
        level1: {
            required: [
                {
                    id: 'second-wind',
                    name: 'Second Wind',
                    description: 'You have a limited well of stamina that you can draw on to protect yourself from harm. On your turn, you can use a bonus action to regain hit points equal to 1d10 + your fighter level.',
                    usageLimit: 'Once per short or long rest',
                    type: 'active',
                    actionType: 'bonus',
                    icon: 'heart-pulse' // For future icons
                }
            ],
            optional: [
                {
                    id: 'fighting-style',
                    name: 'Fighting Style',
                    description: "You adopt a particular style of fighting as your specialty. Choose one of the following options. You can't take a Fighting Style option more than once, even if you later get to choose again.",
                    type: 'passive',
                    choices: [
                        {
                            id: 'archery',
                            name: 'Archery',
                            description: 'You gain a +2 bonus to attack rolls you make with ranged weapons.',
                            benefit: '+2 to attack rolls with ranged weapons',
                            icon: 'bow-arrow'
                        },
                        {
                            id: 'defense',
                            name: 'Defense',
                            description: 'While you are wearing armor, you gain a +1 bonus to AC.',
                            benefit: '+1 to AC when wearing armor',
                            icon: 'shield'
                        },
                        {
                            id: 'dueling',
                            name: 'Dueling',
                            description: 'When you are wielding a melee weapon in one hand and no other weapons, you gain a +2 bonus to damage rolls with that weapon.',
                            benefit: '+2 to damage with one-handed weapons',
                            icon: 'sword'
                        },
                        {
                            id: 'great-weapon-fighting',
                            name: 'Great Weapon Fighting',
                            description: 'When you roll a 1 or 2 on a damage die for an attack you make with a melee weapon that you are wielding with two hands, you can reroll the die and must use the new roll. The weapon must have the two-handed or versatile property for you to gain this benefit.',
                            benefit: 'Reroll 1s and 2s on damage with two-handed weapons',
                            icon: 'axe'
                        },
                        {
                            id: 'protection',
                            name: 'Protection',
                            description: 'When a creature you can see attacks a target other than you that is within 5 feet of you, you can use your reaction to impose disadvantage on the attack roll. You must be wielding a shield.',
                            benefit: 'Use reaction to protect nearby allies when using a shield',
                            icon: 'shield-check'
                        },
                        {
                            id: 'two-weapon-fighting',
                            name: 'Two-Weapon Fighting',
                            description: 'When you engage in two-weapon fighting, you can add your ability modifier to the damage of the second attack.',
                            benefit: 'Add ability modifier to off-hand weapon damage',
                            icon: 'swords'
                        }
                    ]
                }
            ]
        }
    },
    wizard: {
        level1: {
            required: [
                {
                    id: 'spellcasting',
                    name: 'Spellcasting',
                    description: 'As a student of arcane magic, you have a spellbook containing spells that show the first glimmerings of your true power.',
                    type: 'active',
                    spellcasting: {
                        ability: 'intelligence',
                        cantripsKnown: 3,
                        spellsKnown: 6, // Actually prepared spells
                        spellSlots: {
                            level1: 2
                        }
                    }
                },
                {
                    id: 'arcane-recovery',
                    name: 'Arcane Recovery',
                    description: 'You have learned to regain some of your magical energy by studying your spellbook. Once per day when you finish a short rest, you can choose expended spell slots to recover.',
                    usageLimit: 'Once per day',
                    type: 'active',
                    actionType: 'rest'
                }
            ],
            optional: [] // Wizards don't make optional choices at level 1 except for spells
        }
    },
    cleric: {
        level1: {
            required: [
                {
                    id: 'spellcasting',
                    name: 'Spellcasting',
                    description: 'As a conduit for divine power, you can cast cleric spells.',
                    type: 'active',
                    spellcasting: {
                        ability: 'wisdom',
                        cantripsKnown: 3,
                        spellsKnown: 'wisdom modifier + cleric level', // Formula
                        spellSlots: {
                            level1: 2
                        }
                    }
                }
            ],
            optional: [
                {
                    id: 'divine-domain',
                    name: 'Divine Domain',
                    description: 'Choose one domain related to your deity. Your choice grants you domain spells and other features when you choose it at 1st level.',
                    type: 'passive',
                    choices: [
                        {
                            id: 'knowledge',
                            name: 'Knowledge Domain',
                            description: 'The gods of knowledge value learning and understanding above all. Bards and wizards often worship deities of knowledge.',
                            domainSpells: ['command', 'identify'],
                            features: [
                                {
                                    id: 'blessings-of-knowledge',
                                    name: 'Blessings of Knowledge',
                                    description: 'You learn two languages of your choice. You also become proficient in your choice of two of the following skills: Arcana, History, Nature, or Religion. Your proficiency bonus is doubled for any ability check you make that uses either of those skills.'
                                }
                            ]
                        },
                        {
                            id: 'life',
                            name: 'Life Domain',
                            description: 'The Life domain focuses on the vibrant positive energy that sustains all life. Gods of life promote vitality and health.',
                            domainSpells: ['bless', 'cure-wounds'],
                            features: [
                                {
                                    id: 'disciple-of-life',
                                    name: 'Disciple of Life',
                                    description: 'Your healing spells are more effective. Whenever you use a spell of 1st level or higher to restore hit points to a creature, the creature regains additional hit points equal to 2 + the spell\'s level.'
                                }
                            ]
                        }
                        // Additional domains would be added here
                    ]
                }
            ]
        }
    },
    rogue: {
        level1: {
            required: [
                {
                    id: 'sneak-attack',
                    name: 'Sneak Attack',
                    description: 'You know how to strike subtly and exploit a foe\'s distraction. Once per turn, you can deal an extra 1d6 damage to one creature you hit with an attack if you have advantage on the attack roll.',
                    type: 'passive',
                    damage: '1d6'
                },
                {
                    id: 'thieves-cant',
                    name: 'Thieves\' Cant',
                    description: 'During your rogue training you learned thieves\' cant, a secret mix of dialect, jargon, and code that allows you to hide messages in seemingly normal conversation.',
                    type: 'passive'
                }
            ],
            optional: [
                {
                    id: 'expertise',
                    name: 'Expertise',
                    description: 'Choose two of your skill proficiencies, or one of your skill proficiencies and your proficiency with thieves\' tools. Your proficiency bonus is doubled for any ability check you make that uses either of the chosen proficiencies.',
                    type: 'passive',
                    selectCount: 2,
                    selectType: 'skills',
                    selectFrom: 'proficient'
                }
            ]
        }
    },
    bard: {
        level1: {
            required: [
                {
                    id: 'spellcasting',
                    name: 'Spellcasting',
                    description: 'You have learned to untangle and reshape the fabric of reality in harmony with your wishes and music.',
                    type: 'active',
                    spellcasting: {
                        ability: 'charisma',
                        cantripsKnown: 2,
                        spellsKnown: 4,
                        spellSlots: {
                            level1: 2
                        }
                    }
                },
                {
                    id: 'bardic-inspiration',
                    name: 'Bardic Inspiration',
                    description: 'You can inspire others through stirring words or music. To do so, you use a bonus action on your turn to choose one creature other than yourself within 60 feet of you who can hear you. That creature gains one Bardic Inspiration die, a d6.',
                    type: 'active',
                    actionType: 'bonus',
                    usageLimit: 'Charisma modifier times per long rest',
                    inspirationDie: 'd6'
                }
            ],
            optional: [] // Bards don't make optional choices at level 1 except for spells
        }
    }
};

// Step indicator template - use this in each step function
function getStepIndicatorHTML(currentStep) {
    return `
        <div class="step-indicator">
            <div class="step ${currentStep >= 1 ? (currentStep === 1 ? 'active' : 'completed') : ''}">1</div>
            <div class="step ${currentStep >= 2 ? (currentStep === 2 ? 'active' : 'completed') : ''}">2</div>
            <div class="step ${currentStep >= 3 ? (currentStep === 3 ? 'active' : 'completed') : ''}">3</div>
            <div class="step ${currentStep >= 4 ? (currentStep === 4 ? 'active' : 'completed') : ''}">4</div>
            <div class="step ${currentStep >= 5 ? (currentStep === 5 ? 'active' : 'completed') : ''}">5</div>
            <div class="step ${currentStep >= 6 ? (currentStep === 6 ? 'active' : 'completed') : ''}">6</div>
            <div class="step ${currentStep >= 7 ? (currentStep === 7 ? 'active' : 'completed') : ''}">7</div>
            <div class="step ${currentStep >= 8 ? (currentStep === 8 ? 'active' : 'completed') : ''}">8</div>
        </div>
    `;
}

// Hit Die data for each class
const hitDieData = {
    fighter: { die: 'd10', average: 6 },
    wizard: { die: 'd6', average: 4 },
    cleric: { die: 'd8', average: 5 },
    rogue: { die: 'd8', average: 5 },
    bard: { die: 'd8', average: 5 },
    // Add other classes as needed
};

// Function to calculate starting hit points
function calculateStartingHitPoints(characterClass, constitutionScore) {
    if (!characterClass || !hitDieData[characterClass]) {
        return 0;
    }
    
    // Get hit die maximum value
    const hitDie = hitDieData[characterClass].die;
    const maxHitPoints = parseInt(hitDie.substring(1));
    
    // Calculate Constitution modifier
    const constitutionModifier = Math.floor((constitutionScore - 10) / 2);
    
    // Starting hit points = max hit die + Constitution modifier
    return maxHitPoints + constitutionModifier;
}

// Function to simulate rolling a hit die
function rollHitDie(dieType) {
    // Parse the die type (e.g., 'd10' -> 10)
    const sides = parseInt(dieType.substring(1));
    if (isNaN(sides) || sides <= 0) {
        console.error('Invalid die type:', dieType);
        return 1;
    }
    
    // Roll the die (random number between 1 and sides)
    return Math.floor(Math.random() * sides) + 1;
}

// Function to create animated dice roll effect
function animateDiceRoll(elementId, dieType, finalValue, duration = 1000) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const sides = parseInt(dieType.substring(1));
    const fps = 10;
    const frames = duration / (1000 / fps);
    let frame = 0;
    
    // Show the dice element
    element.style.display = 'flex';
    
    // Start animation
    const intervalId = setInterval(() => {
        // Generate random value for animation
        if (frame < frames - 1) {
            const randomValue = Math.floor(Math.random() * sides) + 1;
            element.textContent = randomValue;
        } else {
            // Show final value on last frame
            element.textContent = finalValue;
            clearInterval(intervalId);
            
            // Add a flash effect when the final value is shown
            element.classList.add('dice-result-flash');
            setTimeout(() => {
                element.classList.remove('dice-result-flash');
            }, 500);
        }
        
        frame++;
    }, 1000 / fps);
}

// Equipment data for each class
const equipmentData = {
    fighter: {
        options: [
            {
                id: 'fighter-a',
                title: 'Option A',
                items: [
                    { name: 'Chain mail', type: 'armor', description: 'Heavy armor (AC 16)' },
                    { name: 'Longsword', type: 'weapon', description: 'Martial melee weapon (1d8 slashing)' },
                    { name: 'Shield', type: 'armor', description: '+2 AC' },
                ]
            },
            {
                id: 'fighter-b',
                title: 'Option B',
                items: [
                    { name: 'Leather armor', type: 'armor', description: 'Light armor (AC 11 + DEX)' },
                    { name: 'Longbow', type: 'weapon', description: 'Martial ranged weapon (1d8 piercing)' },
                    { name: '20 Arrows', type: 'ammunition', description: 'For bow' },
                    { name: 'Shortsword', type: 'weapon', description: 'Martial melee weapon (1d6 piercing)' }
                ]
            }
        ],
        standardItems: [
            { name: 'Backpack', type: 'gear', description: 'Holds your items' },
            { name: 'Bedroll', type: 'gear', description: 'For resting' },
            { name: 'Mess kit', type: 'gear', description: 'For eating' },
            { name: 'Tinderbox', type: 'gear', description: 'For lighting fires' },
            { name: '10 Torches', type: 'gear', description: 'Provides light' },
            { name: '10 days of Rations', type: 'gear', description: 'Food for travel' },
            { name: '50 ft Hemp rope', type: 'gear', description: 'Useful tool' },
            { name: 'Waterskin', type: 'gear', description: 'Holds water' }
        ]
    },
    wizard: {
        options: [
            {
                id: 'wizard-a',
                title: 'Option A',
                items: [
                    { name: 'Quarterstaff', type: 'weapon', description: 'Simple melee weapon (1d6 bludgeoning)' },
                ]
            },
            {
                id: 'wizard-b',
                title: 'Option B',
                items: [
                    { name: 'Dagger', type: 'weapon', description: 'Simple melee weapon (1d4 piercing)' },
                ]
            }
        ],
        standardItems: [
            { name: 'Spellbook', type: 'focus', description: 'Contains your spells' },
            { name: 'Arcane focus', type: 'focus', description: 'For casting spells' },
            { name: 'Backpack', type: 'gear', description: 'Holds your items' },
            { name: 'Bedroll', type: 'gear', description: 'For resting' },
            { name: 'Ink (1 ounce bottle)', type: 'gear', description: 'For writing' },
            { name: 'Ink pen', type: 'gear', description: 'For writing' },
            { name: '10 sheets of parchment', type: 'gear', description: 'For writing' },
            { name: 'Little bag of sand', type: 'gear', description: 'For spellcasting' },
            { name: 'Small knife', type: 'gear', description: 'For utility' }
        ]
    },
    cleric: {
        options: [
            {
                id: 'cleric-a',
                title: 'Option A',
                items: [
                    { name: 'Mace', type: 'weapon', description: 'Simple melee weapon (1d6 bludgeoning)' },
                ]
            },
            {
                id: 'cleric-b',
                title: 'Option B',
                items: [
                    { name: 'Warhammer', type: 'weapon', description: 'Martial melee weapon (1d8 bludgeoning)' },
                ]
            }
        ],
        standardItems: [
            { name: 'Scale mail', type: 'armor', description: 'Medium armor (AC 14 + DEX, max 2)' },
            { name: 'Shield', type: 'armor', description: '+2 AC' },
            { name: 'Holy symbol', type: 'focus', description: 'For casting spells' },
            { name: 'Backpack', type: 'gear', description: 'Holds your items' },
            { name: 'Blanket', type: 'gear', description: 'For warmth' },
            { name: '10 candles', type: 'gear', description: 'Provides light' },
            { name: 'Tinderbox', type: 'gear', description: 'For lighting fires' },
            { name: 'Alms box', type: 'gear', description: 'For donations' },
            { name: '2 blocks of incense', type: 'gear', description: 'For rituals' },
            { name: 'Censer', type: 'gear', description: 'For rituals' },
            { name: 'Vestments', type: 'gear', description: 'Ceremonial clothing' },
            { name: '2 days of Rations', type: 'gear', description: 'Food for travel' },
            { name: 'Waterskin', type: 'gear', description: 'Holds water' }
        ]
    },
    rogue: {
        options: [
            {
                id: 'rogue-a',
                title: 'Option A',
                items: [
                    { name: 'Rapier', type: 'weapon', description: 'Martial melee weapon (1d8 piercing, finesse)' },
                ]
            },
            {
                id: 'rogue-b',
                title: 'Option B',
                items: [
                    { name: 'Shortsword', type: 'weapon', description: 'Martial melee weapon (1d6 piercing, finesse)' },
                ]
            }
        ],
        standardItems: [
            { name: 'Shortbow', type: 'weapon', description: 'Simple ranged weapon (1d6 piercing)' },
            { name: '20 Arrows', type: 'ammunition', description: 'For bow' },
            { name: 'Leather armor', type: 'armor', description: 'Light armor (AC 11 + DEX)' },
            { name: 'Two daggers', type: 'weapon', description: 'Simple melee weapon (1d4 piercing, finesse, thrown)' },
            { name: 'Thieves\' tools', type: 'tool', description: 'For picking locks and disarming traps' },
            { name: 'Backpack', type: 'gear', description: 'Holds your items' },
            { name: 'Bag of 1000 ball bearings', type: 'gear', description: 'Can be spilled as an action' },
            { name: '10 feet of string', type: 'gear', description: 'Useful tool' },
            { name: 'Bell', type: 'gear', description: 'Makes noise' },
            { name: '5 candles', type: 'gear', description: 'Provides light' },
            { name: 'Crowbar', type: 'gear', description: 'For prying things open' },
            { name: 'Hammer', type: 'gear', description: 'For hammering' },
            { name: '10 pitons', type: 'gear', description: 'For climbing' },
            { name: 'Hooded lantern', type: 'gear', description: 'Provides light' },
            { name: '2 flasks of oil', type: 'gear', description: 'For lantern' },
            { name: '5 days of Rations', type: 'gear', description: 'Food for travel' },
            { name: 'Tinderbox', type: 'gear', description: 'For lighting fires' },
            { name: 'Waterskin', type: 'gear', description: 'Holds water' }
        ]
    },
    bard: {
        options: [
            {
                id: 'bard-a',
                title: 'Option A',
                items: [
                    { name: 'Rapier', type: 'weapon', description: 'Martial melee weapon (1d8 piercing, finesse)' },
                ]
            },
            {
                id: 'bard-b',
                title: 'Option B',
                items: [
                    { name: 'Longsword', type: 'weapon', description: 'Martial melee weapon (1d8 slashing)' },
                ]
            }
        ],
        standardItems: [
            { name: 'Leather armor', type: 'armor', description: 'Light armor (AC 11 + DEX)' },
            { name: 'Dagger', type: 'weapon', description: 'Simple melee weapon (1d4 piercing, finesse, thrown)' },
            { name: 'Musical instrument', type: 'focus', description: 'For casting spells and performing' },
            { name: 'Backpack', type: 'gear', description: 'Holds your items' },
            { name: 'Bedroll', type: 'gear', description: 'For resting' },
            { name: '5 candles', type: 'gear', description: 'Provides light' },
            { name: '5 days of Rations', type: 'gear', description: 'Food for travel' },
            { name: 'Waterskin', type: 'gear', description: 'Holds water' },
            { name: 'Disguise kit', type: 'tool', description: 'For changing appearance' }
        ]
    }
};

// Function to start character creation
function startCharacterCreation() {
    // Hide main menu and show character creation
    document.getElementById('main-menu').style.display = 'none';
    const characterCreation = document.getElementById('character-creation');
    characterCreation.style.display = 'block';
    
    // Reset character data
    characterData = {
        name: '',
        race: '',
        class: '',
        background: '',
        level: 1,
        abilities: {
            strength: 10,
            dexterity: 10,
            constitution: 10,
            intelligence: 10,
            wisdom: 10,
            charisma: 10
        },
        skills: [],
        equipment: [],
        spells: [],
        features: [],
        description: ''
    };
    
    // Load step 1 (Basic Info)
    loadBasicInfoStep();
}

// Function to load basic info step with sub-race selection
function loadBasicInfoStep() {
    const characterCreation = document.getElementById('character-creation');
    characterCreation.innerHTML = `
        <div class="character-creation-container">
            <div class="col-md-10">
                ${getStepIndicatorHTML(1)}
            
            <div class="card character-card">
                <div class="card-header bg-dark text-light">
                    <h3 class="mb-0">Basic Character Information</h3>
                </div>
                <div class="card-body">
                    <form id="basic-info-form">
                        <div class="mb-3">
                            <label for="character-name" class="form-label">Character Name</label>
                            <input type="text" class="form-control bg-dark text-light" id="character-name" required>
                        </div>
                        
                        <!-- Race Selection -->
                        <div class="mb-4">
                            <label class="form-label">Race</label>
                            <div class="row race-selection">
                                ${Object.keys(raceData).map(race => `
                                    <div class="col-md-4 mb-3">
                                        <div class="card selection-card" data-race="${race}">
                                            <div class="card-body">
                                                <h5 class="card-title">${raceData[race].name}</h5>
                                                <p class="card-text small">${raceData[race].description}</p>
                                                <div class="card-traits small">
                                                    <strong>Traits:</strong> ${raceData[race].traits.join(', ')}
                                                </div>
                                            </div>
                                            <div class="card-footer">
                                                <div class="selected-indicator">
                                                    <i class="bi bi-check-circle-fill"></i> Selected
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                            <input type="hidden" id="selected-race" name="race" required>
                        </div>
                        
                        <!-- Sub-Race Selection (Initially Hidden) -->
                        <div class="mb-4" id="subrace-section" style="display: none;">
                            <label class="form-label">Sub-Race</label>
                            <div class="row subrace-selection" id="subrace-options">
                                <!-- Will be populated dynamically -->
                            </div>
                            <input type="hidden" id="selected-subrace" name="subrace">
                        </div>
                        
                        <!-- Class Selection -->
                        <div class="mb-4">
                            <label class="form-label">Class</label>
                            <div class="row class-selection">
                                ${Object.keys(classData).map(cls => `
                                    <div class="col-md-4 mb-3">
                                        <div class="card selection-card" data-class="${cls}">
                                            <div class="card-body">
                                                <h5 class="card-title">${classData[cls].name}</h5>
                                                <p class="card-text small">${classData[cls].description}</p>
                                                <div class="small">
                                                    <div><strong>Hit Die:</strong> ${classData[cls].hitDie}</div>
                                                    <div><strong>Primary Ability:</strong> ${classData[cls].primaryAbility}</div>
                                                </div>
                                            </div>
                                            <div class="card-footer">
                                                <div class="selected-indicator">
                                                    <i class="bi bi-check-circle-fill"></i> Selected
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                            <input type="hidden" id="selected-class" name="class" required>
                        </div>
                        
                        <!-- Background Selection -->
                        <div class="mb-4">
                            <label class="form-label">Background</label>
                            <div class="row background-selection">
                                ${Object.keys(backgroundData).map(bg => `
                                    <div class="col-md-4 mb-3">
                                        <div class="card selection-card" data-background="${bg}">
                                            <div class="card-body">
                                                <h5 class="card-title">${backgroundData[bg].name}</h5>
                                                <p class="card-text small">${backgroundData[bg].description}</p>
                                                <div class="small">
                                                    <div><strong>Feature:</strong> ${backgroundData[bg].feature}</div>
                                                    <div><strong>Skills:</strong> ${backgroundData[bg].skillProficiencies.join(', ')}</div>
                                                </div>
                                            </div>
                                            <div class="card-footer">
                                                <div class="selected-indicator">
                                                    <i class="bi bi-check-circle-fill"></i> Selected
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                            <input type="hidden" id="selected-background" name="background" required>
                        </div>
                        
                        <div class="text-end">
                            <button type="submit" class="btn btn-primary">Continue to Abilities</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    `;
    
    // Add event listener to form
    document.getElementById('basic-info-form').addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Verify all selections are made
        const raceInput = document.getElementById('selected-race');
        const classInput = document.getElementById('selected-class');
        const backgroundInput = document.getElementById('selected-background');
        
        if (!raceInput.value || !classInput.value || !backgroundInput.value) {
            alert('Please make all selections (Race, Class, and Background) before continuing.');
            return;
        }
        
        // Save data
        characterData.name = document.getElementById('character-name').value;
        characterData.race = raceInput.value;
        characterData.class = classInput.value;
        characterData.background = backgroundInput.value;
        
        // Save subrace if applicable
        const subraceInput = document.getElementById('selected-subrace');
        if (subraceInput && subraceInput.value) {
            characterData.subrace = subraceInput.value;
        } else {
            // Ensure subrace is removed if not applicable
            delete characterData.subrace;
        }
        
        console.log("Character data updated:", characterData);
        
        // Move to next step
        loadAbilityScoresStep();
    });
    
    // Set up card selection for Race
    const raceCards = document.querySelectorAll('.race-selection .selection-card');
    raceCards.forEach(card => {
        card.addEventListener('click', function() {
            // Get the selected race
            const selectedRace = this.dataset.race;
            
            // Remove selected class from all race cards
            raceCards.forEach(c => c.classList.remove('selected'));
            
            // Add selected class to clicked card
            this.classList.add('selected');
            
            // Update hidden input
            document.getElementById('selected-race').value = selectedRace;
            
            // Handle sub-race display
            updateSubraceOptions(selectedRace);
        });
    });
    
    // Set up card selection for Class
    const classCards = document.querySelectorAll('.class-selection .selection-card');
    classCards.forEach(card => {
        card.addEventListener('click', function() {
            // Remove selected class from all class cards
            classCards.forEach(c => c.classList.remove('selected'));
            
            // Add selected class to clicked card
            this.classList.add('selected');
            
            // Update hidden input
            document.getElementById('selected-class').value = this.dataset.class;
        });
    });
    
    // Set up card selection for Background
    const backgroundCards = document.querySelectorAll('.background-selection .selection-card');
    backgroundCards.forEach(card => {
        card.addEventListener('click', function() {
            // Remove selected class from all background cards
            backgroundCards.forEach(c => c.classList.remove('selected'));
            
            // Add selected class to clicked card
            this.classList.add('selected');
            
            // Update hidden input
            document.getElementById('selected-background').value = this.dataset.background;
        });
    });
    
    // Function to update sub-race options based on selected race
    function updateSubraceOptions(race) {
        const subraceSection = document.getElementById('subrace-section');
        const subraceOptions = document.getElementById('subrace-options');
        const selectedSubraceInput = document.getElementById('selected-subrace');
        
        // Clear any previous value
        selectedSubraceInput.value = '';
        
        // Check if the selected race has sub-races
        if (raceData[race] && raceData[race].hasSubraces) {
            // Show the sub-race section
            subraceSection.style.display = 'block';
            
            // Generate sub-race options
            let subraceHTML = '';
            
            // Add a "None" option
            subraceHTML += `
                <div class="col-md-4 mb-3">
                    <div class="card selection-card subrace-card" data-subrace="none">
                        <div class="card-body">
                            <h5 class="card-title">None</h5>
                            <p class="card-text small">Choose no sub-race and use the base race features only.</p>
                        </div>
                        <div class="card-footer">
                            <div class="selected-indicator">
                                <i class="bi bi-check-circle-fill"></i> Selected
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Add each sub-race option
            raceData[race].subraces.forEach(subrace => {
                subraceHTML += `
                    <div class="col-md-4 mb-3">
                        <div class="card selection-card subrace-card" data-subrace="${subrace.id}">
                            <div class="card-body">
                                <h5 class="card-title">${subrace.name}</h5>
                                <p class="card-text small">${subrace.description}</p>
                                <div class="card-traits small">
                                    <strong>Traits:</strong> ${subrace.traits.join(', ')}
                                </div>
                                <div class="small mt-1">
                                    <strong>Ability Bonuses:</strong> ${Object.entries(subrace.abilityScoreIncrease).map(([ability, value]) => 
                                        `+${value} ${ability.charAt(0).toUpperCase() + ability.slice(1)}`
                                    ).join(', ')}
                                </div>
                            </div>
                            <div class="card-footer">
                                <div class="selected-indicator">
                                    <i class="bi bi-check-circle-fill"></i> Selected
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            // Update the sub-race options
            subraceOptions.innerHTML = subraceHTML;
            
            // Set up card selection for sub-races
            const subraceCards = document.querySelectorAll('.subrace-card');
            subraceCards.forEach(card => {
                card.addEventListener('click', function() {
                    // Remove selected class from all subrace cards
                    subraceCards.forEach(c => c.classList.remove('selected'));
                    
                    // Add selected class to clicked card
                    this.classList.add('selected');
                    
                    // Update hidden input
                    selectedSubraceInput.value = this.dataset.subrace;
                });
            });
            
            // Auto-select "None" as default
            const noneCard = document.querySelector('.subrace-card[data-subrace="none"]');
            if (noneCard) {
                noneCard.classList.add('selected');
                selectedSubraceInput.value = 'none';
            }
        } else {
            // Hide the sub-race section for races without sub-races
            subraceSection.style.display = 'none';
            selectedSubraceInput.value = '';
        }
    }
    
    // If character data already exists, populate the form
    if (characterData.name) {
        document.getElementById('character-name').value = characterData.name;
    }
    
    if (characterData.race) {
        const raceCard = document.querySelector(`.race-selection .selection-card[data-race="${characterData.race}"]`);
        if (raceCard) {
            raceCard.classList.add('selected');
            document.getElementById('selected-race').value = characterData.race;
            
            // Update sub-race options
            updateSubraceOptions(characterData.race);
            
            // If sub-race was previously selected, select it again
            if (characterData.subrace) {
                setTimeout(() => {
                    const subraceCard = document.querySelector(`.subrace-card[data-subrace="${characterData.subrace}"]`);
                    if (subraceCard) {
                        subraceCard.classList.add('selected');
                        document.getElementById('selected-subrace').value = characterData.subrace;
                    }
                }, 100);
            }
        }
    }
    
    if (characterData.class) {
        const classCard = document.querySelector(`.class-selection .selection-card[data-class="${characterData.class}"]`);
        if (classCard) {
            classCard.classList.add('selected');
            document.getElementById('selected-class').value = characterData.class;
        }
    }
    
    if (characterData.background) {
        const backgroundCard = document.querySelector(`.background-selection .selection-card[data-background="${characterData.background}"]`);
        if (backgroundCard) {
            backgroundCard.classList.add('selected');
            document.getElementById('selected-background').value = characterData.background;
        }
    }
}

// Function to load ability scores step with proper centering
function loadAbilityScoresStep() {
    const characterCreation = document.getElementById('character-creation');
    characterCreation.innerHTML = `
        <div class="character-creation-container">
            <div class="col-md-8 mx-auto">
                ${getStepIndicatorHTML(2)}
                
                <div class="card character-card">
                    <div class="card-header bg-dark text-light">
                        <h3 class="mb-0">Ability Scores</h3>
                    </div>
                    <div class="card-body">
                        <p>Distribute points to your ability scores. You have 27 points to spend.</p>
                        <p class="text-light">Scores start at 8 and cost 1 point each up to 13, 2 points each from 14-15.</p>
                        
                        <form id="abilities-form">
                            <div class="row mb-3">
                                <div class="col-12 mb-2">
                                    <div class="alert alert-info" id="points-remaining">
                                        Points remaining: <span id="points-count">27</span>
                                    </div>
                                </div>
                                
                                <!-- Points validation alert - initially hidden -->
                                <div class="col-12 mb-2">
                                    <div class="alert alert-danger" id="points-validation-alert" style="display: none;">
                                        You must spend all available points before continuing!
                                    </div>
                                </div>
                                
                                <div class="col-md-4 mb-3">
                                    <div class="ability-container p-3 border rounded">
                                        <label class="form-label">Strength</label>
                                        <div class="d-flex align-items-center">
                                            <button type="button" class="btn btn-sm btn-outline-danger me-2" data-ability="strength" data-action="decrease">-</button>
                                            <input type="number" class="form-control bg-dark text-light text-center" id="ability-strength" value="8" min="8" max="15" readonly>
                                            <button type="button" class="btn btn-sm btn-outline-success ms-2" data-ability="strength" data-action="increase">+</button>
                                        </div>
                                        <small class="text-light">Modifier: <span id="mod-strength">-1</span></small>
                                    </div>
                                </div>
                                
                                <div class="col-md-4 mb-3">
                                    <div class="ability-container p-3 border rounded">
                                        <label class="form-label">Dexterity</label>
                                        <div class="d-flex align-items-center">
                                            <button type="button" class="btn btn-sm btn-outline-danger me-2" data-ability="dexterity" data-action="decrease">-</button>
                                            <input type="number" class="form-control bg-dark text-light text-center" id="ability-dexterity" value="8" min="8" max="15" readonly>
                                            <button type="button" class="btn btn-sm btn-outline-success ms-2" data-ability="dexterity" data-action="increase">+</button>
                                        </div>
                                        <small class="text-light">Modifier: <span id="mod-dexterity">-1</span></small>
                                    </div>
                                </div>
                                
                                <div class="col-md-4 mb-3">
                                    <div class="ability-container p-3 border rounded">
                                        <label class="form-label">Constitution</label>
                                        <div class="d-flex align-items-center">
                                            <button type="button" class="btn btn-sm btn-outline-danger me-2" data-ability="constitution" data-action="decrease">-</button>
                                            <input type="number" class="form-control bg-dark text-light text-center" id="ability-constitution" value="8" min="8" max="15" readonly>
                                            <button type="button" class="btn btn-sm btn-outline-success ms-2" data-ability="constitution" data-action="increase">+</button>
                                        </div>
                                        <small class="text-light">Modifier: <span id="mod-constitution">-1</span></small>
                                    </div>
                                </div>
                                
                                <div class="col-md-4 mb-3">
                                    <div class="ability-container p-3 border rounded">
                                        <label class="form-label">Intelligence</label>
                                        <div class="d-flex align-items-center">
                                            <button type="button" class="btn btn-sm btn-outline-danger me-2" data-ability="intelligence" data-action="decrease">-</button>
                                            <input type="number" class="form-control bg-dark text-light text-center" id="ability-intelligence" value="8" min="8" max="15" readonly>
                                            <button type="button" class="btn btn-sm btn-outline-success ms-2" data-ability="intelligence" data-action="increase">+</button>
                                        </div>
                                        <small class="text-light">Modifier: <span id="mod-intelligence">-1</span></small>
                                    </div>
                                </div>
                                
                                <div class="col-md-4 mb-3">
                                    <div class="ability-container p-3 border rounded">
                                        <label class="form-label">Wisdom</label>
                                        <div class="d-flex align-items-center">
                                            <button type="button" class="btn btn-sm btn-outline-danger me-2" data-ability="wisdom" data-action="decrease">-</button>
                                            <input type="number" class="form-control bg-dark text-light text-center" id="ability-wisdom" value="8" min="8" max="15" readonly>
                                            <button type="button" class="btn btn-sm btn-outline-success ms-2" data-ability="wisdom" data-action="increase">+</button>
                                        </div>
                                        <small class="text-light">Modifier: <span id="mod-wisdom">-1</span></small>
                                    </div>
                                </div>
                                
                                <div class="col-md-4 mb-3">
                                    <div class="ability-container p-3 border rounded">
                                        <label class="form-label">Charisma</label>
                                        <div class="d-flex align-items-center">
                                            <button type="button" class="btn btn-sm btn-outline-danger me-2" data-ability="charisma" data-action="decrease">-</button>
                                            <input type="number" class="form-control bg-dark text-light text-center" id="ability-charisma" value="8" min="8" max="15" readonly>
                                            <button type="button" class="btn btn-sm btn-outline-success ms-2" data-ability="charisma" data-action="increase">+</button>
                                        </div>
                                        <small class="text-light">Modifier: <span id="mod-charisma">-1</span></small>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="row mb-3">
                                <div class="col-12">
                                    <div class="alert alert-secondary">
                                        <h5>Racial Bonuses from ${raceData[characterData.race]?.name || '...'}</h5>
                                        <p id="racial-bonuses">Select a race to see bonuses</p>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="d-flex justify-content-between">
                                <button type="button" class="btn btn-secondary" id="back-to-basic">Back to Character Basics</button>
                                <button type="submit" class="btn btn-primary">Continue to Skills</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Add event listeners for ability score buttons
    setTimeout(() => {
        // Update racial bonuses text
        updateRacialBonuses();
        
        // Set up ability score increase/decrease buttons
        const abilityButtons = document.querySelectorAll('[data-ability]');
        abilityButtons.forEach(button => {
            button.addEventListener('click', handleAbilityButtonClick);
        });
        
        // Set up back button
        document.getElementById('back-to-basic').addEventListener('click', loadBasicInfoStep);
        

        document.getElementById('abilities-form').addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Get points remaining
            const pointsRemaining = parseInt(document.getElementById('points-count').textContent);
            
            // Check if all points are spent
            if (pointsRemaining > 0) {
                // Show validation error
                const validationAlert = document.getElementById('points-validation-alert');
                validationAlert.style.display = 'block';
                
                // Add a shake animation to the alert and points counter
                validationAlert.classList.add('shake-animation');
                document.getElementById('points-remaining').classList.add('shake-animation');
                
                // Remove animation class after animation completes
                setTimeout(() => {
                    validationAlert.classList.remove('shake-animation');
                    document.getElementById('points-remaining').classList.remove('shake-animation');
                }, 500);
                
                // Return early to prevent moving to next step
                return;
            }
            
            // Hide validation message if visible
            const validationAlert = document.getElementById('points-validation-alert');
            if (validationAlert) {
                validationAlert.style.display = 'none';
            }
            
            // Save base ability scores (before racial bonuses)
            const abilities = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma'];
            abilities.forEach(ability => {
                characterData.abilities[ability] = parseInt(document.getElementById(`ability-${ability}`).value);
            });
            
            console.log("Base ability scores (before racial bonuses):", {...characterData.abilities});
            
            // Apply racial ability score bonuses
            applyRacialAbilityBonuses();
            
            console.log("Final ability scores (after racial bonuses):", characterData.abilities);
            
            // Move to next step
            loadSkillsStep();
        });
    }, 100);
}

// Update the function that applies racial ability score bonuses to include sub-races
function applyRacialAbilityBonuses() {
    if (!characterData.race || !raceData[characterData.race]) {
        console.log("No race selected, or race data not found");
        return;
    }
    
    const race = characterData.race;
    const racialBonuses = raceData[race].abilityScoreIncrease;
    
    console.log(`Applying racial bonuses for ${raceData[race].name}:`, racialBonuses);
    
    // Apply base race bonuses
    
    // Apply bonuses to all abilities if the race has an "all" bonus (like humans)
    if (racialBonuses.all) {
        const allBonus = racialBonuses.all;
        console.log(`Applying +${allBonus} to all abilities`);
        
        for (const ability in characterData.abilities) {
            characterData.abilities[ability] += allBonus;
            console.log(`${ability}: ${characterData.abilities[ability] - allBonus} + ${allBonus} = ${characterData.abilities[ability]}`);
        }
    } 
    // Apply specific ability bonuses
    else {
        for (const ability in racialBonuses) {
            const bonus = racialBonuses[ability];
            
            if (characterData.abilities[ability] !== undefined) {
                console.log(`Applying +${bonus} to ${ability}`);
                characterData.abilities[ability] += bonus;
                console.log(`${ability}: ${characterData.abilities[ability] - bonus} + ${bonus} = ${characterData.abilities[ability]}`);
            }
        }
    }
    
    // Apply sub-race bonuses if applicable
    if (characterData.subrace && characterData.subrace !== 'none' && raceData[race].hasSubraces) {
        // Find the selected sub-race
        const subrace = raceData[race].subraces.find(sr => sr.id === characterData.subrace);
        
        if (subrace && subrace.abilityScoreIncrease) {
            console.log(`Applying sub-race bonuses for ${subrace.name}:`, subrace.abilityScoreIncrease);
            
            // Apply sub-race ability score increases
            for (const ability in subrace.abilityScoreIncrease) {
                const bonus = subrace.abilityScoreIncrease[ability];
                
                if (characterData.abilities[ability] !== undefined) {
                    console.log(`Applying +${bonus} to ${ability} from sub-race`);
                    characterData.abilities[ability] += bonus;
                    console.log(`${ability}: ${characterData.abilities[ability] - bonus} + ${bonus} = ${characterData.abilities[ability]}`);
                }
            }
        }
    }
}

// Update the function that displays racial bonuses in the UI
function updateRacialBonuses() {
    const race = characterData.race;
    const racialBonusesElement = document.getElementById('racial-bonuses');
    
    if (!race || !raceData[race]) {
        racialBonusesElement.textContent = 'Select a race to see bonuses';
        return;
    }
    
    const raceInfo = raceData[race];
    let bonusText = '';
    
    if (raceInfo.abilityScoreIncrease.all) {
        bonusText += `+${raceInfo.abilityScoreIncrease.all} to all ability scores. `;
    } else {
        for (const [ability, bonus] of Object.entries(raceInfo.abilityScoreIncrease)) {
            bonusText += `+${bonus} ${ability.charAt(0).toUpperCase() + ability.slice(1)}. `;
        }
    }
    
    bonusText += 'Traits: ' + raceInfo.traits.join(', ');
    racialBonusesElement.textContent = bonusText;
    
    // Optionally, show a preview of what the final scores would be
    const abilities = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma'];
    abilities.forEach(ability => {
        const abilityInput = document.getElementById(`ability-${ability}`);
        const modifierElement = document.getElementById(`mod-${ability}`);
        
        if (abilityInput && modifierElement) {
            // Get the base score
            const baseScore = parseInt(abilityInput.value);
            let racialBonus = 0;
            
            // Calculate the racial bonus
            if (raceInfo.abilityScoreIncrease.all) {
                racialBonus = raceInfo.abilityScoreIncrease.all;
            } else if (raceInfo.abilityScoreIncrease[ability]) {
                racialBonus = raceInfo.abilityScoreIncrease[ability];
            }
            
            // Calculate the final score and modifier
            const finalScore = baseScore + racialBonus;
            const modifier = Math.floor((finalScore - 10) / 2);
            
            // Display the racial bonus and final modifier
            if (racialBonus > 0) {
                modifierElement.innerHTML = `<span class="text-success">${modifier >= 0 ? '+' : ''}${modifier}</span> <small class="text-light">(+${racialBonus} racial)</small>`;
            } else {
                modifierElement.textContent = modifier >= 0 ? `+${modifier}` : modifier;
            }
        }
    });
}

// Function to handle ability score buttons
function handleAbilityButtonClick(e) {
    const ability = e.target.dataset.ability;
    const action = e.target.dataset.action;
    const inputElement = document.getElementById(`ability-${ability}`);
    const modifierElement = document.getElementById(`mod-${ability}`);
    const pointsElement = document.getElementById('points-count');
    
    let currentValue = parseInt(inputElement.value);
    let pointsRemaining = parseInt(pointsElement.textContent);
    
    if (action === 'increase') {
        // Calculate point cost (1 point from 8-13, 2 points from 14-15)
        const pointCost = currentValue >= 13 ? 2 : 1;
        
        if (pointsRemaining >= pointCost && currentValue < 15) {
            currentValue += 1;
            pointsRemaining -= pointCost;
        }
    } else if (action === 'decrease' && currentValue > 8) {
        // Refund points (1 point from 9-13, 2 points from 14-15)
        const pointRefund = currentValue > 13 ? 2 : 1;
        currentValue -= 1;
        pointsRemaining += pointRefund;
    }
    
    // Update values
    inputElement.value = currentValue;
    pointsElement.textContent = pointsRemaining;
    
    // Update modifier
    const modifier = Math.floor((currentValue - 10) / 2);
    modifierElement.textContent = modifier >= 0 ? `+${modifier}` : modifier;
    
    // Update UI based on points remaining
    if (pointsRemaining <= 0) {
        document.querySelectorAll('[data-action="increase"]').forEach(btn => {
            btn.disabled = true;
        });
    } else {
        document.querySelectorAll('[data-action="increase"]').forEach(btn => {
            const abilVal = parseInt(document.getElementById(`ability-${btn.dataset.ability}`).value);
            // Only enable if there are enough points and ability is < 15
            const pointCost = abilVal >= 13 ? 2 : 1;
            btn.disabled = (pointsRemaining < pointCost || abilVal >= 15);
        });
    }
}

// Function to load skills step with proper centering
function loadSkillsStep() {
    const characterCreation = document.getElementById('character-creation');
    characterCreation.innerHTML = `
        <div class="character-creation-container">
            <div class="col-md-8 mx-auto">
                ${getStepIndicatorHTML(3)}
                
                <div class="card character-card">
                    <div class="card-header bg-dark text-light">
                        <h3 class="mb-0">Skills & Proficiencies</h3>
                    </div>
                    <div class="card-body">
                        <p>Select skills based on your class and background.</p>
                        
                        <form id="skills-form">
                            <div class="row mb-3">
                                <div class="col-12">
                                    <div class="alert alert-info">
                                        <h5>${classData[characterData.class]?.name || '...'} Skills</h5>
                                        <p>Choose 2 skills from the list below:</p>
                                        <div id="class-skills">
                                            <!-- Will be populated dynamically -->
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="row mb-3">
                                <div class="col-12">
                                    <div class="alert alert-secondary">
                                        <h5>${backgroundData[characterData.background]?.name || '...'} Skills</h5>
                                        <p>You gain proficiency in the following skills:</p>
                                        <div id="background-skills">
                                            <!-- Will be populated dynamically -->
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="d-flex justify-content-between">
                                <button type="button" class="btn btn-secondary" id="back-to-abilities">Back to Abilities</button>
                                <button type="submit" class="btn btn-primary">Continue to Features</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    setTimeout(() => {
        // Populate class skills
        const classSkillsContainer = document.getElementById('class-skills');
        const selectedClassSkills = classSkills[characterData.class] || [];
        
        if (selectedClassSkills.length > 0) {
            let html = '<div class="row">';
            selectedClassSkills.forEach(skill => {
                html += `
                    <div class="col-md-6 mb-2">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" name="class-skill" id="skill-${skill}" value="${skill}">
                            <label class="form-check-label" for="skill-${skill}">
                                ${skills[skill].name} (${skills[skill].ability.charAt(0).toUpperCase() + skills[skill].ability.slice(1)})
                            </label>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
            classSkillsContainer.innerHTML = html;
            
            // Limit class skill selection to 2
            const classSkillCheckboxes = document.querySelectorAll('input[name="class-skill"]');
            classSkillCheckboxes.forEach(checkbox => {
                checkbox.addEventListener('change', function() {
                    const checkedCount = document.querySelectorAll('input[name="class-skill"]:checked').length;
                    if (checkedCount > 2) {
                        this.checked = false;
                    }
                });
            });
        } else {
            classSkillsContainer.innerHTML = '<p>No class skills available</p>';
        }
        
        // Populate background skills
        const backgroundSkillsContainer = document.getElementById('background-skills');
        const selectedBackground = characterData.background;
        
        if (selectedBackground && backgroundData[selectedBackground]) {
            const bgSkills = backgroundData[selectedBackground].skillProficiencies;
            let html = '<ul class="list-group list-group-flush bg-transparent">';
            bgSkills.forEach(skillName => {
                const skillKey = Object.keys(skills).find(key => 
                    skills[key].name.toLowerCase() === skillName.toLowerCase()
                );
                
                if (skillKey) {
                    html += `<li class="list-group-item bg-transparent">${skills[skillKey].name} (${skills[skillKey].ability.charAt(0).toUpperCase() + skills[skillKey].ability.slice(1)})</li>`;
                }
            });
            html += '</ul>';
            backgroundSkillsContainer.innerHTML = html;
        } else {
            backgroundSkillsContainer.innerHTML = '<p>No background skills available</p>';
        }
        
        // Set up back button
        document.getElementById('back-to-abilities').addEventListener('click', loadAbilityScoresStep);
        
        // Set up form submission
        document.getElementById('skills-form').addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Save selected skills
            const selectedSkills = [];
            document.querySelectorAll('input[name="class-skill"]:checked').forEach(checkbox => {
                selectedSkills.push(checkbox.value);
            });
            
            // Add background skills
            if (characterData.background && backgroundData[characterData.background]) {
                backgroundData[characterData.background].skillProficiencies.forEach(skillName => {
                    const skillKey = Object.keys(skills).find(key => 
                        skills[key].name.toLowerCase() === skillName.toLowerCase()
                    );
                    
                    if (skillKey && !selectedSkills.includes(skillKey)) {
                        selectedSkills.push(skillKey);
                    }
                });
            }
            
            characterData.skills = selectedSkills;
            
            // Move to next step
            loadClassFeaturesStep()
        });
    }, 100);
}

// Fixed continuation from class features to spell selection
function loadClassFeaturesStep() {
    const characterCreation = document.getElementById('character-creation');
    const characterClass = characterData.class;
    
    console.log("Loading class features for:", characterClass);
    
    // Get features for the selected class
    const classFeatureData = classFeatures[characterClass]?.level1 || { required: [], optional: [] };
    
    console.log("Class feature data:", classFeatureData);
    
    // Create HTML for required features with the selection-card style
    let requiredFeaturesHTML = '';
    if (classFeatureData.required && classFeatureData.required.length > 0) {
        requiredFeaturesHTML += '<div class="row">';
        classFeatureData.required.forEach(feature => {
            requiredFeaturesHTML += `
                <div class="col-md-4 mb-3">
                    <div class="selection-card">
                        <div class="card-body">
                            <h5 class="card-title">${feature.name}</h5>
                            <p class="card-text small">${feature.description}</p>
                            <div class="small">
                                ${feature.type === 'active' ? 
                                    `<div><strong>Type:</strong> Active</div>` : 
                                    `<div><strong>Type:</strong> Passive</div>`
                                }
                                ${feature.usageLimit ? 
                                    `<div><strong>Usage:</strong> ${feature.usageLimit}</div>` : 
                                    ''
                                }
                                ${feature.actionType ? 
                                    `<div><strong>Action:</strong> ${feature.actionType}</div>` : 
                                    ''
                                }
                            </div>
                        </div>
                        <div class="card-footer">
                            <div class="feature-type-indicator">
                                <i class="bi ${feature.type === 'active' ? 'bi-lightning-fill' : 'bi-shield-fill'}"></i> 
                                ${feature.type === 'active' ? 'Active Ability' : 'Passive Ability'}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        requiredFeaturesHTML += '</div>';
    }
    
    // Create HTML for optional features that require choices
    let optionalFeaturesHTML = '';
    
    if (classFeatureData.optional && classFeatureData.optional.length > 0) {
        classFeatureData.optional.forEach(featureGroup => {
            optionalFeaturesHTML += `
                <div class="feature-group mb-4">
                    <h4>${featureGroup.name}</h4>
                    <p class="text-light">${featureGroup.description}</p>
            `;
            
            // Handle different types of choices
            if (featureGroup.choices && featureGroup.choices.length > 0) {
                // For choice-based features like Fighting Style - using cards
                optionalFeaturesHTML += `<div class="row feature-choices" data-feature-id="${featureGroup.id}">`;
                
                featureGroup.choices.forEach(choice => {
                    optionalFeaturesHTML += `
                        <div class="col-md-4 mb-3">
                            <div class="selection-card choice-card" data-choice-id="${choice.id}" data-feature-id="${featureGroup.id}">
                                <div class="card-body">
                                    <h5 class="card-title">${choice.name}</h5>
                                    <p class="card-text small">${choice.description}</p>
                                    ${choice.benefit ? `<div class="benefit-tag">${choice.benefit}</div>` : ''}
                                </div>
                                <div class="card-footer">
                                    <div class="selected-indicator">
                                        <i class="bi bi-check-circle-fill"></i> Selected
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                });
                
                optionalFeaturesHTML += `</div>`;
                
                // Hidden input to store selection (updated by card clicks)
                optionalFeaturesHTML += `<input type="hidden" id="${featureGroup.id}-selection" name="${featureGroup.id}-selection" value="">`;
            } else if (featureGroup.selectType === 'skills') {
                // For skill selection features like Rogue's Expertise
                optionalFeaturesHTML += `
                    <div class="skill-selection" data-feature-id="${featureGroup.id}" 
                        data-select-count="${featureGroup.selectCount}">
                    <p class="text-light">Choose ${featureGroup.selectCount} skills to gain expertise in:</p>
                    <div class="row">
                `;
                
                // Get character's proficient skills
                const proficientSkills = characterData.skills || [];
                
                // Add checkboxes for proficient skills
                Object.keys(skills).forEach(skillKey => {
                    if (proficientSkills.includes(skillKey)) {
                        optionalFeaturesHTML += `
                            <div class="col-md-6 col-lg-4 mb-2">
                                <div class="form-check">
                                    <input class="form-check-input expertise-skill-input" type="checkbox" 
                                        name="expertise-skill" id="expertise-${skillKey}" value="${skillKey}">
                                    <label class="form-check-label text-light" for="expertise-${skillKey}">
                                        ${skills[skillKey].name}
                                    </label>
                                </div>
                            </div>
                        `;
                    }
                });
                
                optionalFeaturesHTML += `
                        </div>
                        <div class="expertise-validation-message text-danger mt-2" style="display: none;">
                            Please select exactly ${featureGroup.selectCount} skills.
                        </div>
                    </div>
                `;
            }
            
            optionalFeaturesHTML += `</div>`;
        });
    }
    
    // Build the complete HTML for the Class Features step
    characterCreation.innerHTML = `
        <div class="character-creation-container">
            <div class="col-md-8 mx-auto">
                ${getStepIndicatorHTML(4)}
                
                <div class="card character-card">
                    <div class="card-header bg-dark text-light">
                        <h3 class="mb-0">${classData[characterClass]?.name || 'Class'} Features</h3>
                    </div>
                    <div class="card-body">
                        <form id="class-features-form">
                            <div class="row mb-4">
                                <div class="col-12">
                                    <h4>Class Features</h4>
                                    <p class="text-light">At 1st level, your ${classData[characterClass]?.name || 'character'} gains the following features:</p>
                                    
                                    <div class="required-features">
                                        ${requiredFeaturesHTML || '<p class="text-light">No features available for this class.</p>'}
                                    </div>
                                </div>
                            </div>
                            
                            ${optionalFeaturesHTML ? `
                                <div class="row mb-4">
                                    <div class="col-12">
                                        <h4>Choose Your Features</h4>
                                        <p class="text-light">Select options for your class features:</p>
                                        
                                        <div class="optional-features">
                                            ${optionalFeaturesHTML}
                                        </div>
                                    </div>
                                </div>
                            ` : ''}
                            
                            <div class="d-flex justify-content-between">
                                <button type="button" class="btn btn-secondary" id="back-to-skills">Back to Skills</button>
                                <button type="submit" class="btn btn-primary">Continue to Spells</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Add event listeners
    setTimeout(() => {
        // Set up back button
        document.getElementById('back-to-skills').addEventListener('click', loadSkillsStep);
        
        // Setup Wizard class choice selection
        const classChoiceCards = document.querySelectorAll('.choice-card');
        classChoiceCards.forEach(card => {
            card.addEventListener('click', function() {
                const featureId = this.getAttribute('data-feature-id');
                const choiceId = this.getAttribute('data-choice-id');
                const hiddenInput = document.getElementById(`${featureId}-selection`);
                
                console.log(`Card clicked: ${featureId} - ${choiceId}`);
                
                // Update all cards in the feature group
                document.querySelectorAll(`.choice-card[data-feature-id="${featureId}"]`).forEach(c => {
                    c.classList.remove('selected');
                });
                
                // Add selected class to this card
                this.classList.add('selected');
                
                // Update hidden input with selected value
                if (hiddenInput) {
                    hiddenInput.value = choiceId;
                    console.log(`Updated hidden input ${featureId}-selection to ${choiceId}`);
                } else {
                    console.warn(`Hidden input for ${featureId} not found`);
                }
                
                // Remove needs-selection class if present
                const featureGroup = document.querySelector(`.feature-choices[data-feature-id="${featureId}"]`);
                if (featureGroup) {
                    featureGroup.classList.remove('needs-selection');
                }
            });
        });
        
        // Set up expertise skills for Rogue
        if (characterClass === 'rogue') {
            const expertiseCheckboxes = document.querySelectorAll('.expertise-skill-input');
            const maxSelections = parseInt(document.querySelector('.skill-selection').getAttribute('data-select-count')) || 2;
            
            expertiseCheckboxes.forEach(checkbox => {
                checkbox.addEventListener('change', function() {
                    const checkedCount = document.querySelectorAll('input[name="expertise-skill"]:checked').length;
                    
                    // If too many are checked, uncheck the current one
                    if (checkedCount > maxSelections) {
                        this.checked = false;
                        document.querySelector('.expertise-validation-message').style.display = 'block';
                        document.querySelector('.expertise-validation-message').classList.add('shake-animation');
                        setTimeout(() => {
                            document.querySelector('.expertise-validation-message').classList.remove('shake-animation');
                        }, 500);
                    } else {
                        document.querySelector('.expertise-validation-message').style.display = 'none';
                    }
                });
            });
        }
        
        // Form submission
        const form = document.getElementById('class-features-form');
        if (form) {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                console.log("Class features form submitted");
                
                // Make sure characterData exists
                if (!characterData) {
                    console.error("characterData is undefined!");
                    characterData = {};
                }
                
                // CRITICAL FIX: Make absolutely sure the features objects exist
                if (!characterData.features) {
                    console.log("Creating features object in characterData");
                    characterData.features = {};
                }
                
                if (!characterData.features.required) {
                    console.log("Creating required array in features");
                    characterData.features.required = [];
                }
                
                if (!characterData.features.optional) {
                    console.log("Creating optional object in features");
                    characterData.features.optional = {};
                }
                
                // Store the classFeatureData in a local variable
                const localClassFeatureData = classFeatures[characterClass]?.level1 || { required: [], optional: [] };
                console.log("Local class feature data:", localClassFeatureData);
                
                // Save required features
                if (localClassFeatureData.required && localClassFeatureData.required.length > 0) {
                    characterData.features.required = localClassFeatureData.required.map(feature => feature.id);
                    console.log("Saved required features:", characterData.features.required);
                }
                
                // Process and validate optional features
                let validChoices = true;
                
                if (localClassFeatureData.optional && localClassFeatureData.optional.length > 0) {
                    for (const featureGroup of localClassFeatureData.optional) {
                        if (featureGroup.choices && featureGroup.choices.length > 0) {
                            // Handle choice-based features like Fighting Style
                            const hiddenInput = document.getElementById(`${featureGroup.id}-selection`);
                            
                            if (hiddenInput && hiddenInput.value) {
                                console.log(`Setting ${featureGroup.id} to ${hiddenInput.value}`);
                                characterData.features.optional[featureGroup.id] = hiddenInput.value;
                            } else {
                                // If a choice is required but not selected, prevent continuing
                                validChoices = false;
                                console.log(`Missing selection for ${featureGroup.id}`);
                                
                                // Highlight the feature group that needs attention
                                const featureGroupElement = document.querySelector(`.feature-choices[data-feature-id="${featureGroup.id}"]`);
                                if (featureGroupElement) {
                                    featureGroupElement.classList.add('needs-selection');
                                    featureGroupElement.classList.add('shake-animation');
                                    setTimeout(() => {
                                        featureGroupElement.classList.remove('shake-animation');
                                    }, 500);
                                }
                            }
                        } else if (featureGroup.selectType === 'skills') {
                            // Handle skill selection features like Expertise
                            const selectedSkills = Array.from(document.querySelectorAll('input[name="expertise-skill"]:checked'))
                                .map(input => input.value);
                            
                            // Validate selection count
                            if (selectedSkills.length === featureGroup.selectCount) {
                                characterData.features.optional[featureGroup.id] = selectedSkills;
                                console.log(`Selected expertise skills:`, selectedSkills);
                                
                                if (document.querySelector('.expertise-validation-message')) {
                                    document.querySelector('.expertise-validation-message').style.display = 'none';
                                }
                            } else {
                                validChoices = false;
                                console.log(`Invalid number of expertise skills: ${selectedSkills.length} selected, need ${featureGroup.selectCount}`);
                                
                                // Show validation message
                                if (document.querySelector('.expertise-validation-message')) {
                                    document.querySelector('.expertise-validation-message').style.display = 'block';
                                    document.querySelector('.expertise-validation-message').classList.add('shake-animation');
                                    setTimeout(() => {
                                        document.querySelector('.expertise-validation-message').classList.remove('shake-animation');
                                    }, 500);
                                }
                            }
                        }
                    }
                }
                
                // Debug the final state
                console.log("Final characterData.features:", JSON.stringify(characterData.features));
                
                // If all choices valid, proceed to next step
                if (validChoices) {
                    console.log('All choices valid, proceeding to spell selection step');
                    loadSpellSelectionStep(); // This is the next step
                } else {
                    console.log('Invalid choices, cannot proceed');
                }
            });
        } else {
            console.error("Form not found!");
        }
    }, 100);
}

// Function to check if character gets spells from their race
function checkForRaceBasedSpells() {
    // Check for High Elf
    if (characterData.race === 'elf' && characterData.subrace === 'high-elf') {
        return true;
    }
    
    // Check for other races with innate spells
    // Tiefling, Forest Gnome, etc. could be added here
    
    return false;
}

// Function to get all spell options for a character
function getSpellOptionsForCharacter() {
    const options = {
        cantrips: {
            fromClass: [],
            fromRace: []
        },
        spells: {
            fromClass: [],
            fromRace: []
        },
        selections: {
            // How many of each type to select
            classCantrips: 0,
            classSpells: 0,
            raceCantrips: 0,
            preparedSpells: 0
        }
    };
    
    // Add class-based spell options
    if (['wizard', 'bard', 'cleric', 'sorcerer', 'warlock'].includes(characterData.class)) {
        // Set selection counts
        if (characterData.class === 'wizard') {
            options.selections.classCantrips = 3;
            options.selections.classSpells = 6; // Spellbook
            
            // Prepared spells = INT mod + level
            const intMod = Math.floor((characterData.abilities.intelligence - 10) / 2);
            options.selections.preparedSpells = Math.max(1, intMod + 1);
        } 
        else if (characterData.class === 'bard') {
            options.selections.classCantrips = 2;
            options.selections.classSpells = 4; // Known spells
        }
        // Add other classes as needed
        
        // Get cantrips available from class
        options.cantrips.fromClass = getCantripsForClass(characterData.class);
        
        // Get 1st level spells available from class
        options.spells.fromClass = getSpellsForClassAndLevel(characterData.class, 1);
    }
    
    // Add race-based spell options
    if (characterData.race === 'elf' && characterData.subrace === 'high-elf') {
        // High Elves get one wizard cantrip
        options.selections.raceCantrips = 1;
        options.cantrips.fromRace = getCantripsForClass('wizard');
    }
    
    return options;
}

// Function to check if character gets spells from their race
function checkForRaceBasedSpells() {
    console.log("Checking for race-based spells");
    console.log("Character race:", characterData.race);
    console.log("Character subrace:", characterData.subrace);
    
    // Check for High Elf
    if (characterData.race === 'elf' && characterData.subrace === 'high-elf') {
        console.log("High Elf detected - should have cantrip access");
        return true;
    }
    
    // Check for other races with innate spells
    // Tiefling, Forest Gnome, etc. could be added here
    
    console.log("No race-based spells detected");
    return false;
}

// Function to load spell selection step
function loadSpellSelectionStep() {
    const characterCreation = document.getElementById('character-creation');
    
    // Check for spell access from both class and race
    const hasClassSpells = ['wizard', 'bard', 'cleric', 'sorcerer', 'warlock'].includes(characterData.class);
    const hasRaceSpells = checkForRaceBasedSpells();
    
    console.log("Checking spell access:", { hasClassSpells, hasRaceSpells });
    
    // Initialize spellcasting object if not exists
    if (!characterData.spellcasting) {
        characterData.spellcasting = {
            cantripsKnown: [],
            spellsKnown: [],
            spellsPreparable: [],
            spellsPrepared: [],
            spellSlots: {}
        };
    }
    
    // If no spell access at all, show a simple message and proceed button
    if (!hasClassSpells && !hasRaceSpells) {
        characterCreation.innerHTML = `
            <div class="character-creation-container">
                <div class="col-md-8 mx-auto">
                    ${getStepIndicatorHTML(5)}
                    
                    <div class="card character-card">
                        <div class="card-header bg-dark text-light">
                            <h3 class="mb-0">Spell Selection</h3>
                        </div>
                        <div class="card-body text-center">
                            <div class="my-5">
                                <i class="bi bi-magic" style="font-size: 3rem; color: #6c757d;"></i>
                                <h4 class="mt-3">No Spell Access</h4>
                                <p class="text-light">Your character doesn't have access to any spells at this level.</p>
                                <p class="text-light">As you gain levels, you may gain spell access depending on your class and choices.</p>
                            </div>
                            
                            <div class="d-flex justify-content-between mt-5">
                                <button type="button" class="btn btn-secondary" id="back-to-features">Back to Features</button>
                                <button type="button" class="btn btn-primary" id="continue-to-hit-points">Continue to Hit Points</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Add event listeners
        setTimeout(() => {
            // Back button
            document.getElementById('back-to-features').addEventListener('click', loadClassFeaturesStep);
            
            // Continue button - THIS WAS MISSING
            document.getElementById('continue-to-hit-points').addEventListener('click', loadHitPointStep);
        }, 100);
        
        return; // Add return here to prevent further execution
    }
    
    // Gather all spell options from class and race
    const spellOptions = getSpellOptionsForCharacter();
        
    // Now build the HTML for the spell selection page
    let html = `
        <div class="character-creation-container">
            <div class="col-md-8 mx-auto">
                ${getStepIndicatorHTML(5)}
                
                <div class="card character-card">
                    <div class="card-header bg-dark text-light">
                        <h3 class="mb-0">Spell Selection</h3>
                    </div>
                    <div class="card-body">
                        <form id="spell-selection-form">
    `;
    
    // Add class-based spellcasting sections if applicable
    if (hasClassSpells) {
        html += generateClassSpellcasterHTML();
    }
    
    // Add race-based spell sections if applicable
    if (hasRaceSpells) {
        html += generateRaceSpellcasterHTML();
    }
    
    html += `
                            <div class="d-flex justify-content-between mt-4">
                                <button type="button" class="btn btn-secondary" id="back-to-features">Back to Features</button>
                                <button type="submit" class="btn btn-primary">Continue to Hit Points</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    characterCreation.innerHTML = html;
    
    // Add event listeners
    setTimeout(() => {
        // Back button
        document.getElementById('back-to-features').addEventListener('click', loadClassFeaturesStep);
        
        // Populate class cantrips if applicable
        if (hasClassSpells && document.getElementById('class-cantrips-container')) {
            populateCantrips(
                spellOptions.cantrips.fromClass, 
                spellOptions.selections.classCantrips, 
                'class-cantrips-container', 
                'class-cantrips'
            );
        }
        
        // Populate race cantrips if applicable
        if (hasRaceSpells && document.getElementById('race-cantrips-container')) {
            populateCantrips(
                spellOptions.cantrips.fromRace,
                spellOptions.selections.raceCantrips,
                'race-cantrips-container',
                'race-cantrips'
            );
        }
        
        // Populate class spells if applicable
        if (hasClassSpells && document.getElementById('class-spells-container')) {
            if (characterData.class === 'wizard') {
                populateWizardSpells(
                    spellOptions.spells.fromClass,
                    spellOptions.selections.classSpells,
                    spellOptions.selections.preparedSpells
                );
            } else if (characterData.class === 'bard') {
                populateBardSpells(
                    spellOptions.spells.fromClass,
                    spellOptions.selections.classSpells
                );
            }
            // Add other classes as needed
        }
        
        // Form submission
        document.getElementById('spell-selection-form').addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Validate all selections
            let allSelectionsValid = true;
            let validationMessage = '';
            
            // Validate class cantrips if applicable
            if (hasClassSpells && spellOptions.selections.classCantrips > 0) {
                const selectedClassCantrips = getSelectedSpells('class-cantrips');
                if (selectedClassCantrips.length !== spellOptions.selections.classCantrips) {
                    allSelectionsValid = false;
                    validationMessage = `Please select exactly ${spellOptions.selections.classCantrips} class cantrips.`;
                } else {
                    // Save to character data
                    characterData.spellcasting.cantripsKnown = selectedClassCantrips;
                }
            }
            
            // Validate race cantrips if applicable
            if (hasRaceSpells && spellOptions.selections.raceCantrips > 0) {
                const selectedRaceCantrips = getSelectedSpells('race-cantrips');
                if (selectedRaceCantrips.length !== spellOptions.selections.raceCantrips) {
                    allSelectionsValid = false;
                    validationMessage = `Please select exactly ${spellOptions.selections.raceCantrips} race cantrips.`;
                } else {
                    // Add to character data (combine with class cantrips)
                    characterData.spellcasting.cantripsKnown = [
                        ...(characterData.spellcasting.cantripsKnown || []),
                        ...selectedRaceCantrips
                    ];
                }
            }
            
            // Validate class-specific spell selections
            if (hasClassSpells) {
                if (characterData.class === 'wizard') {
                    const selectedSpellbook = getSelectedSpells('spellbook');
                    const selectedPrepared = getSelectedSpells('prepared');
                    
                    if (selectedSpellbook.length !== spellOptions.selections.classSpells) {
                        allSelectionsValid = false;
                        validationMessage = `Please select exactly ${spellOptions.selections.classSpells} spells for your spellbook.`;
                    } else if (selectedPrepared.length !== spellOptions.selections.preparedSpells) {
                        allSelectionsValid = false;
                        validationMessage = `Please select exactly ${spellOptions.selections.preparedSpells} prepared spells.`;
                    } else if (!selectedPrepared.every(spell => selectedSpellbook.includes(spell))) {
                        allSelectionsValid = false;
                        validationMessage = `You can only prepare spells from your spellbook.`;
                    } else {
                        // Save to character data
                        characterData.spellcasting.spellsPreparable = selectedSpellbook;
                        characterData.spellcasting.spellsPrepared = selectedPrepared;
                    }
                } else if (characterData.class === 'bard') {
                    const selectedSpells = getSelectedSpells('known');
                    
                    if (selectedSpells.length !== spellOptions.selections.classSpells) {
                        allSelectionsValid = false;
                        validationMessage = `Please select exactly ${spellOptions.selections.classSpells} known spells.`;
                    } else {
                        // Save to character data
                        characterData.spellcasting.spellsKnown = selectedSpells;
                        characterData.spellcasting.spellsPrepared = selectedSpells; // For bards, known = prepared
                    }
                }
                // Add other classes as needed
            }
            
            // Show validation error or proceed
            if (!allSelectionsValid) {
                alert(validationMessage); // Replace with better UI feedback if desired
                return;
            }
            
            // Proceed to next step
            loadHitPointStep();
        });
    }, 100);
}

// Function to generate HTML for class-based spellcasting sections
function generateClassSpellcasterHTML() {
    let html = '';
    const characterClass = characterData.class;
    
    if (!['wizard', 'bard', 'cleric', 'sorcerer', 'warlock'].includes(characterClass)) {
        return html; // Not a spellcaster class
    }
    
    // Determine spellcasting ability
    let spellcastingAbility = '';
    if (characterClass === 'wizard') {
        spellcastingAbility = 'intelligence';
    } else if (characterClass === 'bard') {
        spellcastingAbility = 'charisma';
    } else if (characterClass === 'cleric') {
        spellcastingAbility = 'wisdom';
    }
    // Add other classes as needed
    
    // Calculate spell save DC and spell attack bonus
    const abilityScore = characterData.abilities[spellcastingAbility];
    const abilityModifier = Math.floor((abilityScore - 10) / 2);
    const proficiencyBonus = 2; // At 1st level
    
    const spellSaveDC = 8 + proficiencyBonus + abilityModifier;
    const spellAttackBonus = proficiencyBonus + abilityModifier;
    const spellAttackBonusText = spellAttackBonus >= 0 ? `+${spellAttackBonus}` : spellAttackBonus;
    
    // Update spellcasting info in character data
    if (!characterData.spellcasting) {
        characterData.spellcasting = {};
    }
    
    characterData.spellcasting.ability = spellcastingAbility;
    characterData.spellcasting.spellSaveDC = spellSaveDC;
    characterData.spellcasting.spellAttackBonus = spellAttackBonus;
    
    // Add spell slots based on class
    characterData.spellcasting.spellSlots = { 1: 2 }; // Most 1st level casters get 2 slots
    
    // Get spell options
    const spellOptions = getSpellOptionsForCharacter();
    const cantripsCount = spellOptions.selections.classCantrips;
    
    html += `
        <h4 class="mb-3">${classData[characterClass].name} Spellcasting</h4>
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="selection-card">
                    <div class="card-body">
                        <h5 class="card-title">Spellcasting Details</h5>
                        <ul class="list-unstyled">
                            <li><strong>Spellcasting Ability:</strong> ${spellcastingAbility.charAt(0).toUpperCase() + spellcastingAbility.slice(1)}</li>
                            <li><strong>Spell Save DC:</strong> ${spellSaveDC}</li>
                            <li><strong>Spell Attack Bonus:</strong> ${spellAttackBonusText}</li>
                        </ul>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="selection-card">
                    <div class="card-body">
                        <h5 class="card-title">Spell Slots</h5>
                        <div class="spell-slots-display">
                            <div class="spell-slot-level">
                                <div class="slot-level-label">1st</div>
                                <div class="slot-bubbles">
                                    <span class="slot-bubble filled"></span>
                                    <span class="slot-bubble filled"></span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Class Cantrips Section -->
        <div class="mb-4">
            <h5>Class Cantrips</h5>
            <p class="text-light">Choose ${cantripsCount} cantrips from your class list:</p>
            <div id="class-cantrips-container">
                <!-- Will be populated dynamically -->
            </div>
        </div>
    `;
    
    // Add class-specific spell sections
    if (characterClass === 'wizard') {
        const spellbookCount = spellOptions.selections.classSpells;
        const preparedCount = spellOptions.selections.preparedSpells;
        
        html += `
            <div class="mb-4">
                <h5>Wizard Spellbook</h5>
                <p class="text-light">Choose ${spellbookCount} 1st-level wizard spells for your spellbook. 
                You'll then select ${preparedCount} of these to prepare:</p>
                <div id="class-spells-container">
                    <!-- Will be populated dynamically -->
                </div>
            </div>
        `;
    } else if (characterClass === 'bard') {
        const spellsKnownCount = spellOptions.selections.classSpells;
        
        html += `
            <div class="mb-4">
                <h5>Bard Spells</h5>
                <p class="text-light">Choose ${spellsKnownCount} 1st-level bard spells that you know:</p>
                <div id="class-spells-container">
                    <!-- Will be populated dynamically -->
                </div>
            </div>
        `;
    }
    
    return html;
}

// Function to generate HTML for race-based spellcasting
function generateRaceSpellcasterHTML() {
    let html = '';
    
    // Check for High Elf
    if (characterData.race === 'elf' && characterData.subrace === 'high-elf') {
        // Get spell options
        const spellOptions = getSpellOptionsForCharacter();
        const raceCantripsCount = spellOptions.selections.raceCantrips;
        
        html += `
            <div class="mb-4 mt-4 pt-3 border-top">
                <h4 class="mb-3">High Elf Cantrip</h4>
                <p class="text-light">As a High Elf, you know one cantrip of your choice from the wizard spell list:</p>
                <div id="race-cantrips-container">
                    <!-- Will be populated dynamically -->
                </div>
            </div>
        `;
    }
    
    // Add other races with innate spellcasting here
    
    return html;
}

// Spell helper functions
function getCantripsForClass(className) {
    return Object.values(spellData).filter(spell => 
        spell.level === 0 && spell.classes.includes(className)
    );
}

function getSpellsForClassAndLevel(className, level) {
    return Object.values(spellData).filter(spell => 
        spell.level === level && spell.classes.includes(className)
    );
}

function getSpellById(spellId) {
    return spellData[spellId] || null;
}

// Function to populate the cantrips section
function populateCantrips(cantrips, maxSelections, containerId, selectionName) {
    const container = document.getElementById(containerId);
    
    if (!container || !cantrips || cantrips.length === 0) {
        console.error("Cannot populate cantrips:", { container, cantrips });
        return;
    }
    
    // Sort cantrips by name
    cantrips.sort((a, b) => a.name.localeCompare(b.name));
    
    let html = '<div class="row">';
    
    cantrips.forEach(cantrip => {
        html += `
            <div class="col-md-4 mb-3">
                <div class="selection-card" data-spell-id="${cantrip.id}" data-selection="${selectionName}">
                    <div class="card-body">
                        <h5 class="card-title">${cantrip.name}</h5>
                        <p class="card-text small">${cantrip.school} cantrip</p>
                        <div class="card-traits small">
                            <div><strong>Casting Time:</strong> ${cantrip.castingTime}</div>
                            <div><strong>Range:</strong> ${cantrip.range}</div>
                            <div><strong>Duration:</strong> ${cantrip.duration}</div>
                        </div>
                        <div class="spell-description small mt-2">
                            ${cantrip.description.substring(0, 100)}...
                        </div>
                    </div>
                    <div class="card-footer">
                        <div class="selected-indicator">
                            <i class="bi bi-check-circle-fill"></i> Selected
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    html += `
        <input type="hidden" id="${selectionName}-selected" value="">
        <div id="${selectionName}-count" class="alert alert-info mt-3">
            Selected: <span id="${selectionName}-count-value">0</span>/${maxSelections} cantrips
        </div>
    `;
    
    container.innerHTML = html;
    
    // Set up the card selection
    const cards = document.querySelectorAll(`.selection-card[data-selection="${selectionName}"]`);
    let selectedSpells = [];
    
    // Function to update the hidden input and counter
    function updateSelection() {
        document.getElementById(`${selectionName}-selected`).value = selectedSpells.join(',');
        const countSpan = document.getElementById(`${selectionName}-count-value`);
        if (countSpan) {
            countSpan.textContent = selectedSpells.length;
        }
        
        // Update the alert style based on selection count
        const countAlert = document.getElementById(`${selectionName}-count`);
        if (countAlert) {
            if (selectedSpells.length === maxSelections) {
                countAlert.className = 'alert alert-success mt-3';
            } else if (selectedSpells.length > maxSelections) {
                countAlert.className = 'alert alert-danger mt-3';
            } else {
                countAlert.className = 'alert alert-info mt-3';
            }
        }
    }
    
    cards.forEach(card => {
        card.addEventListener('click', function() {
            const spellId = this.getAttribute('data-spell-id');
            const index = selectedSpells.indexOf(spellId);
            
            if (index === -1) {
                // Not selected, so select it if we haven't reached the max
                if (selectedSpells.length < maxSelections) {
                    selectedSpells.push(spellId);
                    this.classList.add('selected');
                } else {
                    // We could show a validation message here
                    return; // Don't allow more than max selections
                }
            } else {
                // Already selected, so deselect it
                selectedSpells.splice(index, 1);
                this.classList.remove('selected');
            }
            
            updateSelection();
        });
    });
    
    // Pre-select cantrips if they exist in character data
    if (characterData.spellcasting && characterData.spellcasting.cantripsKnown) {
        characterData.spellcasting.cantripsKnown.forEach(cantripId => {
            const card = document.querySelector(`.selection-card[data-spell-id="${cantripId}"][data-selection="${selectionName}"]`);
            if (card) {
                const spellId = card.getAttribute('data-spell-id');
                if (!selectedSpells.includes(spellId)) {
                    selectedSpells.push(spellId);
                    card.classList.add('selected');
                }
            }
        });
        updateSelection();
    }
}

// Helper function to get selected spells from a hidden input
function getSelectedSpells(selectionName) {
    const hiddenInput = document.getElementById(`${selectionName}-selected`);
    if (!hiddenInput || !hiddenInput.value) {
        return [];
    }
    return hiddenInput.value.split(',');
}

// Function to populate bard spells
function populateBardSpells(spells, maxSelections) {
    const container = document.getElementById('class-spells-container');
    
    if (!container || !spells || spells.length === 0) {
        console.error("Cannot populate bard spells:", { container, spells });
        return;
    }
    
    // Sort spells by name
    spells.sort((a, b) => a.name.localeCompare(b.name));
    
    let html = '<div class="row">';
    
    spells.forEach(spell => {
        html += `
            <div class="col-md-4 mb-3">
                <div class="selection-card" data-spell-id="${spell.id}" data-selection="known">
                    <div class="card-body">
                        <h5 class="card-title">${spell.name}</h5>
                        <p class="card-text small">${spell.level}st-level ${spell.school.toLowerCase()}</p>
                        <div class="card-traits small">
                            <div><strong>Casting Time:</strong> ${spell.castingTime}</div>
                            <div><strong>Range:</strong> ${spell.range}</div>
                            <div><strong>Duration:</strong> ${spell.duration}</div>
                        </div>
                        <div class="spell-description small mt-2">
                            ${spell.description.substring(0, 100)}...
                        </div>
                    </div>
                    <div class="card-footer">
                        <div class="selected-indicator">
                            <i class="bi bi-check-circle-fill"></i> Selected
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    html += `
        <input type="hidden" id="known-selected" value="">
        <div id="known-count" class="alert alert-info mt-3">
            Selected: <span id="known-count-value">0</span>/${maxSelections} spells
        </div>
    `;
    
    container.innerHTML = html;
    
    // Set up the card selection
    const cards = document.querySelectorAll('.selection-card[data-selection="known"]');
    let selectedSpells = [];
    
    // Function to update the hidden input and counter
    function updateSelection() {
        document.getElementById('known-selected').value = selectedSpells.join(',');
        const countSpan = document.getElementById('known-count-value');
        if (countSpan) {
            countSpan.textContent = selectedSpells.length;
        }
        
        // Update the alert style based on selection count
        const countAlert = document.getElementById('known-count');
        if (countAlert) {
            if (selectedSpells.length === maxSelections) {
                countAlert.className = 'alert alert-success mt-3';
            } else if (selectedSpells.length > maxSelections) {
                countAlert.className = 'alert alert-danger mt-3';
            } else {
                countAlert.className = 'alert alert-info mt-3';
            }
        }
    }
    
    cards.forEach(card => {
        card.addEventListener('click', function() {
            const spellId = this.getAttribute('data-spell-id');
            const index = selectedSpells.indexOf(spellId);
            
            if (index === -1) {
                // Not selected, so select it if we haven't reached the max
                if (selectedSpells.length < maxSelections) {
                    selectedSpells.push(spellId);
                    this.classList.add('selected');
                } else {
                    // Don't allow more than max selections
                    return;
                }
            } else {
                // Already selected, so deselect it
                selectedSpells.splice(index, 1);
                this.classList.remove('selected');
            }
            
            updateSelection();
        });
    });
    
    // Pre-select spells if they exist in character data
    if (characterData.spellcasting && characterData.spellcasting.spellsKnown) {
        characterData.spellcasting.spellsKnown.forEach(spellId => {
            const card = document.querySelector(`.selection-card[data-spell-id="${spellId}"][data-selection="known"]`);
            if (card) {
                const id = card.getAttribute('data-spell-id');
                if (!selectedSpells.includes(id)) {
                    selectedSpells.push(id);
                    card.classList.add('selected');
                }
            }
        });
        updateSelection();
    }
}

// Function to populate wizard spells section
function populateWizardSpells(spells, spellbookMax, preparedMax) {
    const container = document.getElementById('class-spells-container');
    
    if (!container || !spells || spells.length === 0) {
        console.error("Cannot populate wizard spells:", { container, spells });
        return;
    }
    
    // Sort spells by name
    spells.sort((a, b) => a.name.localeCompare(b.name));
    
    let html = `
        <div class="alert alert-info mb-3">
            <strong>Wizard Spellcasting:</strong> First select ${spellbookMax} spells for your spellbook,
            then choose ${preparedMax} of those spells to prepare each day.
        </div>
        
        <h5>Spellbook Selection</h5>
        <div class="row mb-4">
    `;
    
    // Spellbook selection
    spells.forEach(spell => {
        html += `
            <div class="col-md-4 mb-3">
                <div class="selection-card" data-spell-id="${spell.id}" data-selection="spellbook">
                    <div class="card-body">
                        <h5 class="card-title">${spell.name}</h5>
                        <p class="card-text small">${spell.level}st-level ${spell.school.toLowerCase()}</p>
                        <div class="card-traits small">
                            <div><strong>Casting Time:</strong> ${spell.castingTime}</div>
                            <div><strong>Range:</strong> ${spell.range}</div>
                            <div><strong>Duration:</strong> ${spell.duration}</div>
                        </div>
                        <div class="spell-description small mt-2">
                            ${spell.description.substring(0, 100)}...
                        </div>
                    </div>
                    <div class="card-footer">
                        <div class="selected-indicator">
                            <i class="bi bi-check-circle-fill"></i> In Spellbook
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += `
        </div>
        <input type="hidden" id="spellbook-selected" value="">
        <div id="spellbook-count" class="alert alert-info mt-3 mb-4">
            Selected: <span id="spellbook-count-value">0</span>/${spellbookMax} spells in spellbook
        </div>
        
        <h5>Prepared Spells</h5>
        <p class="text-light">Choose which spells to prepare from your spellbook:</p>
        <div id="prepared-spells-container" class="mb-3">
            <div class="alert alert-secondary">
                Select spells for your spellbook first.
            </div>
        </div>
        <input type="hidden" id="prepared-selected" value="">
    `;
    
    container.innerHTML = html;
    
    // Set up the spellbook selection
    const spellbookCards = document.querySelectorAll('.selection-card[data-selection="spellbook"]');
    let spellbookSelected = [];
    let preparedSelected = [];
    
    // Function to update spellbook selection UI
    function updateSpellbookSelection() {
        document.getElementById('spellbook-selected').value = spellbookSelected.join(',');
        const countSpan = document.getElementById('spellbook-count-value');
        if (countSpan) {
            countSpan.textContent = spellbookSelected.length;
        }
        
        // Update the alert style
        const countAlert = document.getElementById('spellbook-count');
        if (countAlert) {
            if (spellbookSelected.length === spellbookMax) {
                countAlert.className = 'alert alert-success mt-3 mb-4';
            } else if (spellbookSelected.length > spellbookMax) {
                countAlert.className = 'alert alert-danger mt-3 mb-4';
            } else {
                countAlert.className = 'alert alert-info mt-3 mb-4';
            }
        }
        
        // Update prepared spells container when spellbook changes
        updatePreparedSpellsUI();
    }
    
    // Function to update the prepared spells UI
    function updatePreparedSpellsUI() {
        const preparedContainer = document.getElementById('prepared-spells-container');
        
        if (spellbookSelected.length === 0) {
            preparedContainer.innerHTML = `
                <div class="alert alert-secondary">
                    Select spells for your spellbook first.
                </div>
            `;
            return;
        }
        
        let preparedHtml = '<div class="row">';
        
        // For each spell in the spellbook, create a card for prepared selection
        spellbookSelected.forEach(spellId => {
            const spell = spells.find(s => s.id === spellId);
            if (spell) {
                preparedHtml += `
                    <div class="col-md-4 mb-3">
                        <div class="selection-card ${preparedSelected.includes(spellId) ? 'selected' : ''}" 
                             data-spell-id="${spellId}" data-selection="prepared">
                            <div class="card-body">
                                <h5 class="card-title">${spell.name}</h5>
                                <p class="card-text small">${spell.level}st-level ${spell.school.toLowerCase()}</p>
                                <div class="spell-description small mt-2">
                                    ${spell.description.substring(0, 75)}...
                                </div>
                            </div>
                            <div class="card-footer">
                                <div class="selected-indicator">
                                    <i class="bi bi-check-circle-fill"></i> Prepared
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }
        });
        
        preparedHtml += `
            </div>
            <div id="prepared-count" class="alert alert-info mt-3">
                Selected: <span id="prepared-count-value">${preparedSelected.length}</span>/${preparedMax} prepared spells
            </div>
        `;
        
        preparedContainer.innerHTML = preparedHtml;
        
        // Update prepared spells counter style
        const preparedCount = document.getElementById('prepared-count');
        if (preparedCount) {
            if (preparedSelected.length === preparedMax) {
                preparedCount.className = 'alert alert-success mt-3';
            } else if (preparedSelected.length > preparedMax) {
                preparedCount.className = 'alert alert-danger mt-3';
            } else {
                preparedCount.className = 'alert alert-info mt-3';
            }
        }
        
        // Add click handlers to prepared spell cards
        const preparedCards = document.querySelectorAll('.selection-card[data-selection="prepared"]');
        preparedCards.forEach(card => {
            card.addEventListener('click', function() {
                const spellId = this.getAttribute('data-spell-id');
                const index = preparedSelected.indexOf(spellId);
                
                if (index === -1) {
                    // Not prepared, so prepare it if we haven't reached the max
                    if (preparedSelected.length < preparedMax) {
                        preparedSelected.push(spellId);
                        this.classList.add('selected');
                    } else {
                        // Don't allow more than max selections
                        return;
                    }
                } else {
                    // Already prepared, so unprepare it
                    preparedSelected.splice(index, 1);
                    this.classList.remove('selected');
                }
                
                // Update prepared selection
                document.getElementById('prepared-selected').value = preparedSelected.join(',');
                
                // Update counter
                const countSpan = document.getElementById('prepared-count-value');
                if (countSpan) {
                    countSpan.textContent = preparedSelected.length;
                }
                
                // Update counter style
                const countAlert = document.getElementById('prepared-count');
                if (countAlert) {
                    if (preparedSelected.length === preparedMax) {
                        countAlert.className = 'alert alert-success mt-3';
                    } else if (preparedSelected.length > preparedMax) {
                        countAlert.className = 'alert alert-danger mt-3';
                    } else {
                        countAlert.className = 'alert alert-info mt-3';
                    }
                }
            });
        });
    }
    
    // Add click handlers to spellbook cards
    spellbookCards.forEach(card => {
        card.addEventListener('click', function() {
            const spellId = this.getAttribute('data-spell-id');
            const index = spellbookSelected.indexOf(spellId);
            
            if (index === -1) {
                // Not in spellbook, so add it if we haven't reached the max
                if (spellbookSelected.length < spellbookMax) {
                    spellbookSelected.push(spellId);
                    this.classList.add('selected');
                } else {
                    // Don't allow more than max selections
                    return;
                }
            } else {
                // Already in spellbook, so remove it
                spellbookSelected.splice(index, 1);
                this.classList.remove('selected');
                
                // Also remove from prepared spells if it was prepared
                const preparedIndex = preparedSelected.indexOf(spellId);
                if (preparedIndex !== -1) {
                    preparedSelected.splice(preparedIndex, 1);
                }
            }
            
            updateSpellbookSelection();
        });
    });
    
    // Pre-select spellbook spells if they exist in character data
    if (characterData.spellcasting && characterData.spellcasting.spellsPreparable) {
        spellbookSelected = [...characterData.spellcasting.spellsPreparable];
        
        // Mark the cards as selected
        spellbookSelected.forEach(spellId => {
            const card = document.querySelector(`.selection-card[data-spell-id="${spellId}"][data-selection="spellbook"]`);
            if (card) {
                card.classList.add('selected');
            }
        });
        
        // Also pre-select prepared spells
        if (characterData.spellcasting.spellsPrepared) {
            preparedSelected = [...characterData.spellcasting.spellsPrepared].filter(id => 
                spellbookSelected.includes(id)
            );
        }
        
        updateSpellbookSelection();
    }
}

// Main function to populate spells based on character class
function populateSpells(spells, characterClass, knownCount, spellbookCount, preparedCount) {
    if (characterClass === 'bard') {
        populateSpellsForBard(spells, knownCount);
    } else if (characterClass === 'wizard') {
        populateSpellsForWizard(spells, spellbookCount, preparedCount);
    }
}

// Add a function to generate the spells HTML for the finish step
function generateSpellsHTML() {
    if (!characterData.spellcasting) {
        return '';
    }

    let spellsHTML = '';
    const characterClass = characterData.class;
    
    // If character isn't a spellcaster, don't display anything
    if (!['wizard', 'bard'].includes(characterClass)) {
        return '';
    }
    
    // Get the spellcasting ability and spellcasting modifier
    const spellcastingAbility = characterData.spellcasting.ability;
    const abilityScore = characterData.abilities[spellcastingAbility];
    const abilityModifier = Math.floor((abilityScore - 10) / 2);
    
    // If cantrips are known, display them
    if (characterData.spellcasting.cantripsKnown && characterData.spellcasting.cantripsKnown.length > 0) {
        spellsHTML += `
            <div class="mb-3">
                <h5>Cantrips</h5>
                <div class="row">
        `;
        
        // Convert cantrip IDs to actual spell objects
        const cantrips = characterData.spellcasting.cantripsKnown.map(id => getSpellById(id)).filter(Boolean);
        
        // Sort cantrips by name
        cantrips.sort((a, b) => a.name.localeCompare(b.name));
        
        // Generate HTML for each cantrip
        cantrips.forEach(cantrip => {
            spellsHTML += `
                <div class="col-md-4 mb-2">
                    <div class="spell-summary p-2">
                        <strong>${cantrip.name}</strong>
                        <div class="small text-light">${cantrip.school} cantrip</div>
                    </div>
                </div>
            `;
        });
        
        spellsHTML += `
                </div>
            </div>
        `;
    }
    
    // If spells are known/prepared, display them
    let spellsArray = [];
    
    if (characterClass === 'bard' && characterData.spellcasting.spellsKnown) {
        spellsArray = characterData.spellcasting.spellsKnown.map(id => getSpellById(id)).filter(Boolean);
    } else if (characterClass === 'wizard' && characterData.spellcasting.spellsPrepared) {
        spellsArray = characterData.spellcasting.spellsPrepared.map(id => getSpellById(id)).filter(Boolean);
    }
    
    if (spellsArray.length > 0) {
        // Sort spells by level, then by name
        spellsArray.sort((a, b) => {
            if (a.level !== b.level) {
                return a.level - b.level;
            }
            return a.name.localeCompare(b.name);
        });
        
        spellsHTML += `
            <div class="mb-3">
                <h5>${characterClass === 'bard' ? 'Known Spells' : 'Prepared Spells'}</h5>
                <div class="row">
        `;
        
        // Generate HTML for each spell
        spellsArray.forEach(spell => {
            spellsHTML += `
                <div class="col-md-4 mb-2">
                    <div class="spell-summary p-2">
                        <strong>${spell.name}</strong>
                        <div class="small text-light">${spell.level}st level ${spell.school.toLowerCase()}</div>
                    </div>
                </div>
            `;
        });
        
        spellsHTML += `
                </div>
            </div>
        `;
    }
    
    // Show spellbook for wizards
    if (characterClass === 'wizard' && characterData.spellcasting.spellsPreparable) {
        const spellbook = characterData.spellcasting.spellsPreparable.map(id => getSpellById(id)).filter(Boolean);
        
        if (spellbook.length > 0 && spellbook.length > spellsArray.length) {
            // Filter out already displayed prepared spells
            const preparedSpellIds = characterData.spellcasting.spellsPrepared || [];
            const unpreparedSpells = spellbook.filter(spell => !preparedSpellIds.includes(spell.id));
            
            if (unpreparedSpells.length > 0) {
                // Sort by name
                unpreparedSpells.sort((a, b) => a.name.localeCompare(b.name));
                
                spellsHTML += `
                    <div class="mb-3">
                        <h5>Spellbook (Unprepared)</h5>
                        <div class="row">
                `;
                
                // Generate HTML for each unprepared spell
                unpreparedSpells.forEach(spell => {
                    spellsHTML += `
                        <div class="col-md-4 mb-2">
                            <div class="spell-summary p-2 unprepared">
                                <strong>${spell.name}</strong>
                                <div class="small text-light">${spell.level}st level ${spell.school.toLowerCase()}</div>
                            </div>
                        </div>
                    `;
                });
                
                spellsHTML += `
                        </div>
                    </div>
                `;
            }
        }
    }
    
    // Display spellcasting information
    const spellcastingHTML = `
        <div class="row mb-3">
            <div class="col-md-6">
                <div class="spellcasting-summary p-3">
                    <h5>Spellcasting</h5>
                    <div><strong>Spellcasting Ability:</strong> ${spellcastingAbility.charAt(0).toUpperCase() + spellcastingAbility.slice(1)}</div>
                    <div><strong>Spell Save DC:</strong> ${characterData.spellcasting.spellSaveDC}</div>
                    <div><strong>Spell Attack Bonus:</strong> ${characterData.spellcasting.spellAttackBonus >= 0 ? '+' : ''}${characterData.spellcasting.spellAttackBonus}</div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="spell-slots-summary p-3">
                    <h5>Spell Slots</h5>
                    <div class="slot-level">
                        <span class="slot-label">1st Level:</span>
                        <span class="slot-value">${characterData.spellcasting.spellSlots?.[1] || 0} slots</span>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    return characterClass === 'wizard' || characterClass === 'bard' ? 
        `<div class="spells-section">
            ${spellcastingHTML}
            ${spellsHTML}
        </div>` : '';
}

function generateSpellsHTML() {
    if (!characterData.spellcasting) {
        return '';
    }
    
    const characterClass = characterData.class;
    
    // If character isn't a spellcaster, don't display anything
    if (!['wizard', 'bard', 'cleric'].includes(characterClass)) {
        return '';
    }
    
    // Get the spellcasting ability and stats
    const spellcastingAbility = characterData.spellcasting.ability;
    const abilityScore = characterData.abilities[spellcastingAbility];
    const abilityModifier = Math.floor((abilityScore - 10) / 2);
    
    let spellsHTML = '';
    
    // Spellcasting information
    spellsHTML += `
        <div class="row mb-3">
            <div class="col-md-6">
                <div class="selection-card">
                    <div class="card-body">
                        <h5 class="card-title">Spellcasting</h5>
                        <div class="small">
                            <p>Your spellcasting ability is <strong>${spellcastingAbility.charAt(0).toUpperCase() + spellcastingAbility.slice(1)}</strong>.</p>
                            <ul class="list-unstyled">
                                <li><strong>Spell Save DC:</strong> ${characterData.spellcasting.spellSaveDC}</li>
                                <li><strong>Spell Attack Bonus:</strong> +${characterData.spellcasting.spellAttackBonus}</li>
                            </ul>
                        </div>
                    </div>
                    <div class="card-footer">
                        <div class="feature-type-indicator">
                            <i class="bi bi-magic"></i> ${classData[characterClass]?.name || 'Class'} Spellcasting
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="selection-card">
                    <div class="card-body">
                        <h5 class="card-title">Spell Slots</h5>
                        <div class="spell-slots-display">
                            ${Object.entries(characterData.spellcasting.spellSlots || {}).map(([level, slots]) => `
                                <div class="spell-slot-level mb-2">
                                    <div class="slot-level-label">Level ${level}</div>
                                    <div class="slot-bubbles">
                                        ${Array(slots).fill('<span class="slot-bubble filled"></span>').join('')}
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    <div class="card-footer">
                        <div class="feature-type-indicator">
                            <i class="bi bi-lightning"></i> Spell Energy
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Display cantrips
    if (characterData.spellcasting.cantripsKnown && characterData.spellcasting.cantripsKnown.length > 0) {
        spellsHTML += `
            <div class="row mb-3">
                <div class="col-12">
                    <h5>Cantrips</h5>
                    <div class="row">
        `;
        
        const cantrips = characterData.spellcasting.cantripsKnown.map(id => getSpellById(id)).filter(Boolean);
        
        cantrips.forEach(cantrip => {
            spellsHTML += `
                <div class="col-md-4 mb-2">
                    <div class="selection-card">
                        <div class="card-body">
                            <h5 class="card-title">${cantrip.name}</h5>
                            <div class="spell-properties small">
                                <div><strong>School:</strong> ${cantrip.school}</div>
                                <div><strong>Casting Time:</strong> ${cantrip.castingTime}</div>
                                <div><strong>Range:</strong> ${cantrip.range}</div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        spellsHTML += `
                    </div>
                </div>
            </div>
        `;
    }
    
    // Display prepared/known spells
    const preparedSpells = characterClass === 'wizard' ? 
        (characterData.spellcasting.spellsPrepared || []) : 
        (characterData.spellcasting.spellsKnown || []);
    
    if (preparedSpells.length > 0) {
        spellsHTML += `
            <div class="row mb-3">
                <div class="col-12">
                    <h5>${characterClass === 'wizard' ? 'Prepared Spells' : 'Known Spells'}</h5>
                    <div class="row">
        `;
        
        const spells = preparedSpells.map(id => getSpellById(id)).filter(Boolean);
        
        spells.forEach(spell => {
            spellsHTML += `
                <div class="col-md-4 mb-2">
                    <div class="selection-card">
                        <div class="card-body">
                            <h5 class="card-title">${spell.name}</h5>
                            <div class="spell-properties small">
                                <div><strong>Level:</strong> ${spell.level}</div>
                                <div><strong>School:</strong> ${spell.school}</div>
                                <div><strong>Casting Time:</strong> ${spell.castingTime}</div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        spellsHTML += `
                    </div>
                </div>
            </div>
        `;
    }
    
    // For wizards, show unprepared spellbook spells
    if (characterClass === 'wizard' && characterData.spellcasting.spellsPreparable) {
        const unpreparedSpells = characterData.spellcasting.spellsPreparable
            .filter(id => !characterData.spellcasting.spellsPrepared.includes(id))
            .map(id => getSpellById(id))
            .filter(Boolean);
        
        if (unpreparedSpells.length > 0) {
            spellsHTML += `
                <div class="row mb-3">
                    <div class="col-12">
                        <h5>Spellbook (Unprepared)</h5>
                        <div class="row">
            `;
            
            unpreparedSpells.forEach(spell => {
                spellsHTML += `
                    <div class="col-md-4 mb-2">
                        <div class="selection-card">
                            <div class="card-body">
                                <h5 class="card-title">${spell.name}</h5>
                                <div class="spell-properties small">
                                    <div><strong>Level:</strong> ${spell.level}</div>
                                    <div><strong>School:</strong> ${spell.school}</div>
                                </div>
                            </div>
                            <div class="card-footer">
                                <div class="feature-type-indicator text-light">
                                    <i class="bi bi-book"></i> Not Prepared
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            spellsHTML += `
                        </div>
                    </div>
                </div>
            `;
        }
    }
    
    return spellsHTML;
}

function updateSpellsInCharacterSheet() {
    const characterSheet = document.getElementById('characterSheet');
    if (!characterSheet || !characterData.spellcasting) return;
    
    // Find where to insert the spells section
    let spellsSection = `
        <div class="spells-section mt-3">
            <h5>Spellcasting</h5>
            <div class="small mb-2">
                <div><strong>Ability:</strong> ${characterData.spellcasting.ability.charAt(0).toUpperCase() + characterData.spellcasting.ability.slice(1)}</div>
                <div><strong>DC:</strong> ${characterData.spellcasting.spellSaveDC}</div>
                <div><strong>Attack:</strong> ${characterData.spellcasting.spellAttackBonus >= 0 ? '+' : ''}${characterData.spellcasting.spellAttackBonus}</div>
            </div>
    `;
    
    // Add cantrips
    if (characterData.spellcasting.cantripsKnown && characterData.spellcasting.cantripsKnown.length > 0) {
        spellsSection += `<div class="mt-2"><strong>Cantrips:</strong> `;
        const cantrips = characterData.spellcasting.cantripsKnown.map(id => {
            const spell = getSpellById(id);
            return spell ? spell.name : id;
        });
        spellsSection += cantrips.join(', ');
        spellsSection += `</div>`;
    }
    
    // Add known/prepared spells
    const preparedSpells = characterData.class === 'wizard' ? 
        (characterData.spellcasting.spellsPrepared || []) : 
        (characterData.spellcasting.spellsKnown || []);
    
    if (preparedSpells.length > 0) {
        spellsSection += `<div class="mt-1"><strong>${characterData.class === 'wizard' ? 'Prepared' : 'Known'} Spells:</strong> `;
        const spells = preparedSpells.map(id => {
            const spell = getSpellById(id);
            return spell ? spell.name : id;
        });
        spellsSection += spells.join(', ');
        spellsSection += `</div>`;
    }
    
    // Add spell slots
    if (characterData.spellcasting.spellSlots) {
        spellsSection += `<div class="mt-1"><strong>Spell Slots:</strong> `;
        for (const [level, slots] of Object.entries(characterData.spellcasting.spellSlots)) {
            if (slots > 0) {
                spellsSection += `Level ${level} (${slots}) `;
            }
        }
        spellsSection += `</div>`;
    }
    
    spellsSection += `</div>`;
    
    // Insert the spells section into the character sheet
    characterSheet.innerHTML += spellsSection;
}

// Function to load hit point calculator step with proper dice rolling
function loadHitPointStep() {
    const characterCreation = document.getElementById('character-creation');
    const characterClass = characterData.class;
    const constitutionScore = characterData.abilities.constitution;
    
    // Calculate Constitution modifier
    const constitutionModifier = Math.floor((constitutionScore - 10) / 2);
    const modifierText = constitutionModifier >= 0 ? `+${constitutionModifier}` : constitutionModifier;
    
    // Get hit die information
    const hitDie = hitDieData[characterClass]?.die || 'd8';
    const hitDieMax = parseInt(hitDie.substring(1));
    
    // Calculate starting hit points (max hit die + CON modifier)
    const maxHP = hitDieMax + constitutionModifier;
    
    // Build the HTML for the hit point calculator
    characterCreation.innerHTML = `
        <div class="character-creation-container">
            <div class="col-md-8 mx-auto">
                ${getStepIndicatorHTML(6)}
                
                <div class="card character-card">
                    <div class="card-header bg-dark text-light">
                        <h3 class="mb-0">Hit Points</h3>
                    </div>
                    <div class="card-body">
                        <form id="hit-points-form">
                            <div class="row mb-4">
                                <div class="col-12">
                                    <h4>Starting Hit Points</h4>
                                    <p class="text-light">At 1st level, you start with the maximum hit points from your class's hit die plus your Constitution modifier.</p>
                                    
                                    <div class="hit-points-calculator p-4 border rounded mb-4">
                                        <div class="row align-items-center">
                                            <div class="col-md-4 text-center mb-3 mb-md-0">
                                                <h5>${classData[characterClass]?.name || 'Class'} Hit Die</h5>
                                                <div class="hit-die-display">
                                                    ${hitDie}
                                                </div>
                                            </div>
                                            
                                            <div class="col-md-2 text-center mb-3 mb-md-0">
                                                <h5>Maximum</h5>
                                                <div class="hit-die-value">
                                                    ${hitDieMax}
                                                </div>
                                            </div>
                                            
                                            <div class="col-md-2 text-center mb-3 mb-md-0">
                                                <h5>CON Mod</h5>
                                                <div class="con-modifier">
                                                    ${modifierText}
                                                </div>
                                            </div>
                                            
                                            <div class="col-md-4 text-center">
                                                <h5>Starting HP</h5>
                                                <div class="starting-hp" id="final-hp-display">
                                                    ${maxHP}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div class="dice-roller text-center mb-4">
                                        <h4>Level 2 Preview</h4>
                                        <p class="text-light">See what your hit points might be when you reach level 2.</p>
                                        <p class="text-light">When you level up, you'll roll your hit die and add your Constitution modifier to your max HP.</p>
                                        
                                        <div class="dice-container mb-3">
                                            <div id="dice-display" class="dice" style="display: none;">
                                                1
                                            </div>
                                        </div>
                                        
                                        <button type="button" id="roll-hit-die" class="btn btn-primary" ${characterData.hitPoints?.levelUpRoll ? 'disabled' : ''}>
                                            <i class="bi bi-dice-6"></i> Roll ${hitDie}
                                        </button>
                                        
                                        <div id="roll-result" class="mt-3" ${characterData.hitPoints?.levelUpRoll ? '' : 'style="display: none;"'}>
                                            <p class="mb-0">You rolled <span id="roll-value">${characterData.hitPoints?.levelUpRoll || 0}</span></p>
                                            <p>With CON modifier: <span id="roll-total">${(characterData.hitPoints?.levelUpRoll || 0) + constitutionModifier}</span></p>
                                            <p class="text-light">At level 2, your hit points would be <strong>${maxHP + (characterData.hitPoints?.levelUpRoll || 0) + constitutionModifier}</strong></p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="d-flex justify-content-between">
                                <button type="button" class="btn btn-secondary" id="back-to-features">Back to Features</button>
                                <button type="submit" class="btn btn-primary">Continue to Equipment</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Add event listeners
    setTimeout(() => {
        // Back button
        const backButton = document.getElementById('back-to-features');
        if (backButton) {
            backButton.addEventListener('click', loadSpellSelectionStep);
        } else {
            console.error("Back button not found!");
        }
        
        // Hit die roll button
        const rollButton = document.getElementById('roll-hit-die');
        if (rollButton) {
            rollButton.addEventListener('click', function() {
                // Roll the hit die
                const result = rollHitDie(hitDie);
                
                // Animate the dice roll
                animateDiceRoll('dice-display', hitDie, result);
                
                // Calculate total with Constitution modifier
                const total = result + constitutionModifier;
                
                // Save the roll to character data
                if (!characterData.hitPoints) {
                    characterData.hitPoints = {
                        max: maxHP,
                        current: maxHP
                    };
                }
                
                // Store the level-up roll
                characterData.hitPoints.levelUpRoll = result;
                
                // Update result display
                const rollResult = document.getElementById('roll-result');
                const rollValue = document.getElementById('roll-value');
                const rollTotal = document.getElementById('roll-total');
                
                rollValue.textContent = result;
                rollTotal.textContent = total;
                rollResult.style.display = 'block';
                rollResult.querySelector('p:last-child').innerHTML = 
                    `At level 2, your hit points would be <strong>${maxHP + result + constitutionModifier}</strong>`;
                
                // Disable the roll button after one roll
                this.disabled = true;
                this.innerHTML = '<i class="bi bi-dice-6"></i> Roll Saved';
                
                console.log("Level up roll saved:", characterData.hitPoints.levelUpRoll);
            });
        } else {
            console.error("Roll button not found!");
        }
        
        // Form submission
        const form = document.getElementById('hit-points-form');
        if (form) {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                
                // Save hit points to character data if not already saved
                if (!characterData.hitPoints) {
                    characterData.hitPoints = {
                        max: maxHP,
                        current: maxHP,
                        hitDie: hitDie,
                        level: 1
                    };
                } else {
                    // Update any missing properties
                    characterData.hitPoints.max = maxHP;
                    characterData.hitPoints.current = maxHP;
                    characterData.hitPoints.hitDie = hitDie;
                    characterData.hitPoints.level = 1;
                }
                
                console.log("Hit points saved:", characterData.hitPoints);
                
                // Proceed to next step (Equipment)
                loadEquipmentStep();
            });
        } else {
            console.error("Hit points form not found!");
        }
        
        // If we already have a level up roll, show it
        if (characterData.hitPoints?.levelUpRoll) {
            const rollResult = document.getElementById('roll-result');
            if (rollResult) {
                rollResult.style.display = 'block';
                const rollValue = document.getElementById('roll-value');
                if (rollValue) rollValue.textContent = characterData.hitPoints.levelUpRoll;
                const rollTotal = document.getElementById('roll-total');
                if (rollTotal) rollTotal.textContent = characterData.hitPoints.levelUpRoll + constitutionModifier;
            }
        }
    }, 100);
}

// Function to load equipment selection step
function loadEquipmentStep() {
    const characterCreation = document.getElementById('character-creation');
    const characterClass = characterData.class;
    
    // Get equipment options for the selected class
    const classEquipment = equipmentData[characterClass] || { options: [], standardItems: [] };
    
    // Build the HTML for the equipment selection
    characterCreation.innerHTML = `
        <div class="character-creation-container">
            <div class="col-md-8 mx-auto">
                ${getStepIndicatorHTML(7)}
                
                <div class="card character-card">
                    <div class="card-header bg-dark text-light">
                        <h3 class="mb-0">Equipment Selection</h3>
                    </div>
                    <div class="card-body">
                        <form id="equipment-form">
                            <div class="row mb-4">
                                <div class="col-12">
                                    <h4>Choose Your Equipment</h4>
                                    <p class="text-light">Select one of the available equipment options for your ${classData[characterClass]?.name || 'character'}.</p>
                                    
                                    <div class="equipment-options">
                                        ${classEquipment.options.length > 0 ? `
                                            <div class="row equipment-selection mb-4">
                                                ${classEquipment.options.map(option => `
                                                    <div class="col-md-6 mb-3">
                                                        <div class="selection-card equipment-card" data-equipment="${option.id}">
                                                            <div class="card-body">
                                                                <h5 class="card-title">${option.title}</h5>
                                                                <ul class="equipment-list small">
                                                                    ${option.items.map(item => `
                                                                        <li>
                                                                            <strong>${item.name}</strong>
                                                                            <div class="text-light small">${item.description}</div>
                                                                        </li>
                                                                    `).join('')}
                                                                </ul>
                                                            </div>
                                                            <div class="card-footer">
                                                                <div class="selected-indicator">
                                                                    <i class="bi bi-check-circle-fill"></i> Selected
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                `).join('')}
                                            </div>
                                            <input type="hidden" id="selected-equipment" name="equipment">
                                        ` : '<p class="text-light">No equipment options available for this class.</p>'}
                                    </div>
                                </div>
                            </div>
                            
                            <div class="row mb-4">
                                <div class="col-12">
                                    <h4>Standard Equipment</h4>
                                    <p class="text-light">Your ${classData[characterClass]?.name || 'character'} automatically starts with the following equipment:</p>
                                    
                                    <div class="standard-equipment">
                                        <div class="row">
                                            ${classEquipment.standardItems.map(item => `
                                                <div class="col-md-6 mb-2">
                                                    <div class="standard-item p-2">
                                                        <strong>${item.name}</strong>
                                                        <div class="text-light small">${item.description}</div>
                                                    </div>
                                                </div>
                                            `).join('')}
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="d-flex justify-content-between">
                                <button type="button" class="btn btn-secondary" id="back-to-hit-points">Back to Hit Points</button>
                                <button type="submit" class="btn btn-primary">Continue to Finish</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Add event listeners
    setTimeout(() => {
        // Back button
        const backButton = document.getElementById('back-to-hit-points');
        if (backButton) {
            backButton.addEventListener('click', loadHitPointStep);
        } else {
            console.error("Back button not found!");
        }
        
        // Equipment selection
        const equipmentCards = document.querySelectorAll('.equipment-card');
        if (equipmentCards.length > 0) {
            equipmentCards.forEach(card => {
                card.addEventListener('click', function() {
                    // Remove selected class from all equipment cards
                    equipmentCards.forEach(c => c.classList.remove('selected'));
                    
                    // Add selected class to clicked card
                    this.classList.add('selected');
                    
                    // Update hidden input
                    const selectedEquipmentInput = document.getElementById('selected-equipment');
                    if (selectedEquipmentInput) {
                        selectedEquipmentInput.value = this.dataset.equipment;
                    }
                });
            });
            
            // Auto-select the first equipment option if available
            if (equipmentCards.length > 0) {
                equipmentCards[0].classList.add('selected');
                const selectedEquipmentInput = document.getElementById('selected-equipment');
                if (selectedEquipmentInput) {
                    selectedEquipmentInput.value = equipmentCards[0].dataset.equipment;
                }
            }
        }
        
        // Form submission
        const form = document.getElementById('equipment-form');
        if (form) {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                
                // Get selected equipment option
                const selectedEquipmentInput = document.getElementById('selected-equipment');
                const selectedEquipmentId = selectedEquipmentInput ? selectedEquipmentInput.value : null;
                
                // Find the selected equipment option
                const selectedOption = classEquipment.options.find(option => option.id === selectedEquipmentId);
                
                // Save equipment to character data
                characterData.equipment = {
                    selected: selectedOption ? selectedOption.items : [],
                    standard: classEquipment.standardItems || []
                };
                
                console.log("Equipment saved:", characterData.equipment);
                
                // Proceed to finish step
                loadFinishStep();
            });
        } else {
            console.error("Equipment form not found!");
        }
    }, 100);
}

// Function to generate equipment HTML for the finish step
function generateEquipmentHTML() {
    if (!characterData.equipment) {
        return '<p class="text-light">No equipment selected.</p>';
    }
    
    let equipmentHTML = '<div class="row">';
    
    // Selected equipment option
    if (characterData.equipment.selected && characterData.equipment.selected.length > 0) {
        equipmentHTML += `
            <div class="col-md-6 mb-3">
                <div class="equipment-summary">
                    <h5>Chosen Equipment</h5>
                    <ul class="equipment-list">
                        ${characterData.equipment.selected.map(item => `
                            <li>
                                <strong>${item.name}</strong>
                                <div class="text-light small">${item.description}</div>
                            </li>
                        `).join('')}
                    </ul>
                </div>
            </div>
        `;
    }
    
    // Standard equipment
    if (characterData.equipment.standard && characterData.equipment.standard.length > 0) {
        equipmentHTML += `
            <div class="col-md-6 mb-3">
                <div class="equipment-summary">
                    <h5>Standard Equipment</h5>
                    <ul class="equipment-list">
                        ${characterData.equipment.standard.map(item => `
                            <li>
                                <strong>${item.name}</strong>
                            </li>
                        `).join('')}
                    </ul>
                </div>
            </div>
        `;
    }
    
    equipmentHTML += '</div>';
    return equipmentHTML;
}

// Complete loadFinishStep function with spell section integration
function loadFinishStep() {
    const characterCreation = document.getElementById('character-creation');
    
    // Get class feature data for display
    const classFeatureData = classFeatures[characterData.class]?.level1 || { required: [], optional: [] };
    let featuresHTML = '';
    
    // Build features HTML with consistent card style
    if (characterData.features) {
        // Display required features
        if (characterData.features.required && characterData.features.required.length > 0) {
            featuresHTML += '<div class="mb-4"><h5>Class Features</h5><div class="row">';
            
            characterData.features.required.forEach(featureId => {
                const feature = classFeatureData.required.find(f => f.id === featureId);
                if (feature) {
                    featuresHTML += `
                        <div class="col-md-4 mb-3">
                            <div class="selection-card">
                                <div class="card-body">
                                    <h5 class="card-title">${feature.name}</h5>
                                    <p class="card-text small">${feature.description}</p>
                                    <div class="small">
                                        ${feature.type === 'active' ? 
                                            `<div><strong>Type:</strong> Active</div>` : 
                                            `<div><strong>Type:</strong> Passive</div>`
                                        }
                                        ${feature.usageLimit ? 
                                            `<div><strong>Usage:</strong> ${feature.usageLimit}</div>` : 
                                            ''
                                        }
                                        ${feature.actionType ? 
                                            `<div><strong>Action:</strong> ${feature.actionType}</div>` : 
                                            ''
                                        }
                                    </div>
                                </div>
                                <div class="card-footer">
                                    <div class="feature-type-indicator">
                                        <i class="bi ${feature.type === 'active' ? 'bi-lightning-fill' : 'bi-shield-fill'}"></i> 
                                        ${feature.type === 'active' ? 'Active Ability' : 'Passive Ability'}
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                }
            });
            
            featuresHTML += '</div></div>';
        }
        
        // Display optional features
        if (characterData.features.optional && Object.keys(characterData.features.optional).length > 0) {
            featuresHTML += '<div class="mb-4"><h5>Chosen Options</h5><div class="row">';
            
            for (const [featureId, choiceId] of Object.entries(characterData.features.optional)) {
                const featureGroup = classFeatureData.optional.find(f => f.id === featureId);
                
                if (featureGroup) {
                    if (featureGroup.choices) {
                        // For single-choice features like Fighting Style
                        const choice = featureGroup.choices.find(c => c.id === choiceId);
                        if (choice) {
                            featuresHTML += `
                                <div class="col-md-4 mb-3">
                                    <div class="selection-card selected">
                                        <div class="card-body">
                                            <h5 class="card-title">${choice.name}</h5>
                                            <p class="card-text small">${choice.description}</p>
                                            ${choice.benefit ? 
                                                `<div class="small">
                                                    <strong>Benefit:</strong> ${choice.benefit}
                                                </div>` : 
                                                ''
                                            }
                                        </div>
                                        <div class="card-footer">
                                            <div class="selected-indicator">
                                                <i class="bi bi-check-circle-fill"></i> ${featureGroup.name} Option
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            `;
                        }
                    } else if (Array.isArray(choiceId)) {
                        // For multi-selection features like Expertise
                        const skillNames = choiceId.map(skillId => skills[skillId]?.name).filter(Boolean);
                        
                        featuresHTML += `
                            <div class="col-md-4 mb-3">
                                <div class="selection-card selected">
                                    <div class="card-body">
                                        <h5 class="card-title">${featureGroup.name}</h5>
                                        <p class="card-text small">${featureGroup.description}</p>
                                        <div class="small mt-2">
                                            <strong>Selected Skills:</strong>
                                            <ul class="mb-0 ps-3">
                                                ${skillNames.map(name => `<li>${name}</li>`).join('')}
                                            </ul>
                                        </div>
                                    </div>
                                    <div class="card-footer">
                                        <div class="selected-indicator">
                                            <i class="bi bi-check-circle-fill"></i> Skill Expertise
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `;
                    }
                }
            }
            
            featuresHTML += '</div></div>';
        }
    }
    
    characterCreation.innerHTML = `
        <div class="character-creation-container">
            <div class="col-md-8 mx-auto">
                ${getStepIndicatorHTML(8)}
                
                <div class="card character-card">
                    <div class="card-header bg-dark text-light">
                        <h3 class="mb-0">Review & Finish</h3>
                    </div>
                    <div class="card-body">
                        <div class="row mb-4">
                            <div class="col-md-6">
                                <h4>Character Details</h4>
                                <table class="table table-dark table-sm">
                                    <tr>
                                        <td><strong>Name:</strong></td>
                                        <td>${characterData.name}</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Race:</strong></td>
                                        <td>${raceData[characterData.race]?.name || '—'}
                                            ${characterData.subrace && characterData.subrace !== 'none' ? 
                                                `(${raceData[characterData.race]?.subraces.find(sr => sr.id === characterData.subrace)?.name || ''})` : 
                                                ''}
                                        </td>
                                    </tr>
                                    <tr>
                                        <td><strong>Class:</strong></td>
                                        <td>${classData[characterData.class]?.name || '—'}</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Background:</strong></td>
                                        <td>${backgroundData[characterData.background]?.name || '—'}</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Level:</strong></td>
                                        <td>${characterData.level}</td>
                                    </tr>
                                </table>
                            </div>
                            

                            <div class="col-md-6">
                                <h4>Ability Scores</h4>
                                <div class="row">
                                ${Object.entries(characterData.abilities).map(([ability, score]) => {
                                    const modifier = Math.floor((score - 10) / 2);
                                    const modText = modifier >= 0 ? `+${modifier}` : modifier;
                                    
                                    // Use standard D&D ability abbreviations instead of full names
                                    let abilityAbbrev;
                                    switch(ability) {
                                        case 'strength': abilityAbbrev = 'STR'; break;
                                        case 'dexterity': abilityAbbrev = 'DEX'; break;
                                        case 'constitution': abilityAbbrev = 'CON'; break;
                                        case 'intelligence': abilityAbbrev = 'INT'; break;
                                        case 'wisdom': abilityAbbrev = 'WIS'; break;
                                        case 'charisma': abilityAbbrev = 'CHA'; break;
                                        default: abilityAbbrev = ability.substr(0, 3).toUpperCase();
                                    }
                                    
                                    return `
                                        <div class="col-md-4 col-6 mb-2">
                                            <div class="ability-score">
                                                <div class="ability-name">${abilityAbbrev}</div>
                                                <div class="ability-value">${score}</div>
                                                <div class="ability-modifier">${modText}</div>
                                            </div>
                                        </div>
                                    `;
                                }).join('')}
                                </div>
                            </div>
                        </div>
                        
                       

                        <div class="row mb-4">
                            <div class="col-12">
                                <h4>Hit Points</h4>
                                <div class="hp-summary-container">
                                    <div class="row align-items-center">
                                        <div class="col-md-6 text-center">
                                            <div class="max-hp-display">
                                                <div class="max-hp-title">Maximum HP</div>
                                                <div class="max-hp-value">${characterData.hitPoints?.max || 0}</div>
                                            </div>
                                        </div>
                                        
                                        <div class="d-none d-md-block col-md-1">
                                            <div class="hp-divider h-100"></div>
                                        </div>
                                        
                                        <div class="col-md-5 text-center">
                                            <div class="hit-die-display">
                                                <div class="hit-die-title">Hit Die</div>
                                                <div class="hit-die-label">${hitDieData[characterData.class]?.die || 'd8'}</div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="row mb-4">
                            <div class="col-12">
                                <h4>Equipment</h4>
                                <div class="equipment-summary-container">
                                    ${generateEquipmentHTML()}
                                </div>
                            </div>
                        </div>

                        <div class="row mb-4">
                            <div class="col-12">
                                <h4>Skills</h4>
                                <div class="row" id="skill-list">
                                    <!-- Skill badges will be added here dynamically -->
                                </div>
                            </div>
                        </div>
                        
                        <div class="row mb-4">
                            <div class="col-12">
                                <h4>Features</h4>
                                <div class="features-summary">
                                    ${featuresHTML || '<p class="text-light">No features selected.</p>'}
                                </div>
                            </div>
                        </div>
                        
                        ${['wizard', 'bard', 'cleric'].includes(characterData.class) ? `
                        <div class="row mb-4">
                            <div class="col-12">
                                <h4>Spells</h4>
                                <div class="spells-summary-container">
                                    ${characterData.spellcasting ? generateSpellsHTML() : '<p class="text-light">No spells available for this character.</p>'}
                                </div>
                            </div>
                        </div>
                        ` : ''}
                        
                        <div class="row mb-4">
                            <div class="col-12">
                                <h4>Racial Features</h4>
                                <div class="racial-features-summary">
                                    ${generateRacialFeaturesHTML()}
                                </div>
                            </div>
                        </div>
                        
                        <div class="row mb-4">
                            <div class="col-12">
                                <h4>Character Description</h4>
                                <textarea class="form-control bg-dark text-light" id="character-description" rows="3" placeholder="Add a brief description of your character..."></textarea>
                            </div>
                        </div>
                        
                        <div class="d-flex justify-content-between">
                            <button type="button" class="btn btn-secondary" id="back-to-equipment">Back to Equipment</button>
                            <button type="button" class="btn btn-success" id="finish-creation">Start Adventure!</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    setTimeout(() => {
        // Set up back button
        document.getElementById('back-to-equipment').addEventListener('click', loadEquipmentStep);
        
        // Populate skills list
        const skillListDiv = document.getElementById('skill-list');
        if (skillListDiv && characterData.skills && characterData.skills.length > 0) {
            let skillsHtml = '';
            
            characterData.skills.forEach(skill => {
                skillsHtml += `
                    <div class="col-md-4 col-6 mb-2">
                        <span class="badge bg-success">${skills[skill]?.name || skill}</span>
                    </div>
                `;
            });
            
            skillListDiv.innerHTML = skillsHtml;
        }
        
        // Save description when changed
        document.getElementById('character-description').addEventListener('input', function(e) {
            characterData.description = e.target.value;
        });
        
        // Set up finish button
        document.getElementById('finish-creation').addEventListener('click', finishCharacterCreation);
    }, 100);
}

// Function to save character to the database via the API
function saveCharacterToDatabase() {
    console.log("Attempting to save character to database...");
    
    // Create a clean copy of the character data to avoid any circular references
    // and remove any functions or complex objects that might cause serialization issues
    const cleanCharacterData = JSON.parse(JSON.stringify(characterData));
    
    // Log the data being sent for debugging
    console.log("Character data being sent:", cleanCharacterData);
    
    return new Promise((resolve, reject) => {
        // Make API call to the server endpoint
        fetch('/api/save-character', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(cleanCharacterData)
        })
        .then(response => {
            console.log("Server response status:", response.status);
            
            // Even if response is not OK, get the response body for debugging
            return response.text().then(text => {
                if (response.ok) {
                    try {
                        return JSON.parse(text);
                    } catch (e) {
                        console.error("Error parsing successful response:", e);
                        console.log("Raw response text:", text);
                        throw new Error("Could not parse server response");
                    }
                } else {
                    console.error("Server error response:", text);
                    throw new Error(`Server returned ${response.status}: ${response.statusText}`);
                }
            });
        })
        .then(data => {
            if (data.success) {
                console.log(`Character saved successfully with ID: ${data.character_id}`);
                // Store the character_id in the characterData object
                characterData.character_id = data.character_id;
                resolve(data.character_id);
            } else {
                console.error("Error saving character:", data.error);
                reject(new Error(data.error || "Unknown error saving character"));
            }
        })
        .catch(error => {
            console.error("Network or server error saving character:", error);
            reject(error);
        });
    });
}

// Updated finishCharacterCreation function that continues even if database save fails
async function finishCharacterCreation() {
    // Save final character description if any
    const descriptionElement = document.getElementById('character-description');
    if (descriptionElement) {
        characterData.description = descriptionElement.value;
    }
    
    try {
        // Attempt to save character to database
        await saveCharacterToDatabase();
        console.log("Character successfully saved to database");
    } catch (error) {
        console.error("Error saving character to database:", error);
        
        // Continue with the game even if database save fails
        // Show a notification to the user, but don't block progress
        const errorMessage = document.createElement('div');
        errorMessage.style.position = 'fixed';
        errorMessage.style.bottom = '20px';
        errorMessage.style.right = '20px';
        errorMessage.style.padding = '10px 20px';
        errorMessage.style.backgroundColor = 'rgba(200,50,50,0.9)';
        errorMessage.style.color = 'white';
        errorMessage.style.borderRadius = '5px';
        errorMessage.style.zIndex = '9999';
        errorMessage.style.boxShadow = '0 2px 8px rgba(0,0,0,0.2)';
        errorMessage.textContent = "Character saved locally but couldn't be saved to the server.";
        
        document.body.appendChild(errorMessage);
        
        // Remove the notification after 5 seconds
        setTimeout(() => {
            document.body.removeChild(errorMessage);
        }, 5000);
    }
    
    // Set the active character for the chat interface
    if (window.setActiveCharacter) {
        window.setActiveCharacter(characterData);
        console.log('Set active character for adventure:', characterData.name);
    } else {
        console.warn('setActiveCharacter function not available, falling back to localStorage');
        // Fallback: store in localStorage directly
        localStorage.setItem('activeCharacter', JSON.stringify(characterData));
    }
    
    // Update the character sheet with all data including spells
    updateCharacterSheet();
    
    // Hide character creation and show game interface
    document.getElementById('character-creation').style.display = 'none';
    document.getElementById('game-interface').style.display = 'flex';
    
    // Clear the chat window and add introduction message
    const chatWindow = document.getElementById('chatWindow');
    chatWindow.innerHTML = '';
    
    // Add welcome message
    const welcomeMessage = document.createElement('div');
    welcomeMessage.classList.add('message', 'dm-message');
    
    // Include spellcasting information in the welcome message if applicable
    let spellcastingInfo = '';
    if (characterData.spellcasting && ['wizard', 'bard', 'cleric'].includes(characterData.class)) {
        spellcastingInfo = ` As a ${classData[characterData.class]?.name || 'spellcaster'}, you have access to powerful magic.`;
    }
    
    welcomeMessage.innerHTML = `
        <p>Welcome, brave ${characterData.name}! Your adventure as a ${raceData[characterData.race]?.name || ''} 
        ${classData[characterData.class]?.name || ''} is about to begin.${spellcastingInfo} What would you like to do first?</p>
    `;
    chatWindow.appendChild(welcomeMessage);
    
    // Scroll to bottom of chat
    chatWindow.scrollTop = chatWindow.scrollHeight;
    
    // Send initial message to the AI to start the adventure with this character
    sendInitialMessageToAI(characterData);
}

// Function to generate an introduction for the AI to understand the character
function getCharacterIntroForAI() {
    let intro = `I am ${characterData.name}, a level ${characterData.level} ${raceData[characterData.race]?.name || ''} ${classData[characterData.class]?.name || ''} with a ${backgroundData[characterData.background]?.name || ''} background.`;
    
    // Add ability scores
    intro += ` My ability scores are: `;
    for (const [ability, score] of Object.entries(characterData.abilities)) {
        const modifier = Math.floor((score - 10) / 2);
        const modText = modifier >= 0 ? `+${modifier}` : `${modifier}`;
        intro += `${ability.charAt(0).toUpperCase() + ability.slice(1)} ${score} (${modText}), `;
    }
    
    // Add skills
    if (characterData.skills && characterData.skills.length > 0) {
        intro += ` I am proficient in the following skills: `;
        const skillNames = characterData.skills.map(skill => skills[skill]?.name || skill);
        intro += skillNames.join(', ') + '.';
    }
    
    // Add class features
    const featuresSummary = getFeaturesSummary(characterData);
    intro += featuresSummary;
    
    // Add spellcasting information if applicable
    if (characterData.spellcasting && ['wizard', 'bard', 'cleric'].includes(characterData.class)) {
        intro += ` I am a spellcaster with ${characterData.spellcasting.ability} as my spellcasting ability. `;
        
        // Add cantrips
        if (characterData.spellcasting.cantripsKnown && characterData.spellcasting.cantripsKnown.length > 0) {
            intro += `I know the following cantrips: `;
            const cantrips = characterData.spellcasting.cantripsKnown.map(id => {
                const spell = getSpellById(id);
                return spell ? spell.name : id;
            });
            intro += cantrips.join(', ') + '. ';
        }
        
        // Add known/prepared spells
        const preparedSpells = characterData.class === 'wizard' ? 
            (characterData.spellcasting.spellsPrepared || []) : 
            (characterData.spellcasting.spellsKnown || []);
        
        if (preparedSpells.length > 0) {
            intro += `I ${characterData.class === 'wizard' ? 'have prepared' : 'know'} the following spells: `;
            const spells = preparedSpells.map(id => {
                const spell = getSpellById(id);
                return spell ? spell.name : id;
            });
            intro += spells.join(', ') + '. ';
        }
    }
    
    // Add character description if available
    if (characterData.description) {
        intro += ` ${characterData.description}`;
    }
    
    intro += ` Please start my adventure!`;
    
    return intro;
}

// Function to update the character sheet in the sidebar
function updateCharacterSheet() {
    const characterSheet = document.getElementById('characterSheet');
    
    if (!characterSheet) return;
    
    let html = `
        <div class="character-header mb-3">
            <h4 class="text-center">${characterData.name}</h4>
            <p class="text-center text-light">Level ${characterData.level} ${raceData[characterData.race]?.name || ''} ${classData[characterData.class]?.name || ''}</p>
        </div>
    `;
    
    // Add ability scores
    html += '<div class="ability-scores mb-3"><div class="row">';
    
    Object.entries(characterData.abilities).forEach(([ability, score]) => {
        const modifier = Math.floor((score - 10) / 2);
        const modText = modifier >= 0 ? `+${modifier}` : modifier;
        
        // Use standard D&D ability abbreviations
        let abilityAbbrev;
        switch(ability) {
            case 'strength': abilityAbbrev = 'STR'; break;
            case 'dexterity': abilityAbbrev = 'DEX'; break;
            case 'constitution': abilityAbbrev = 'CON'; break;
            case 'intelligence': abilityAbbrev = 'INT'; break;
            case 'wisdom': abilityAbbrev = 'WIS'; break;
            case 'charisma': abilityAbbrev = 'CHA'; break;
            default: abilityAbbrev = ability.substr(0, 3).toUpperCase();
        }
        
        html += `
            <div class="col-4 mb-2">
                <div class="ability-score">
                    <div class="ability-name">${abilityAbbrev}</div>
                    <div class="ability-value">${score}</div>
                    <div class="ability-modifier">${modText}</div>
                </div>
            </div>
        `;
    });
    
    html += '</div></div>';
    
    // Add hit points display
    if (characterData.hitPoints) {
        html += `
            <div class="hit-points-display mb-3">
                <div class="hp-header d-flex justify-content-between align-items-center">
                    <span>Hit Points</span>
                    <span class="hit-die-small">${hitDieData[characterData.class]?.die || 'd8'}</span>
                </div>
                <div class="hp-bar">
                    <div class="current-hp">${characterData.hitPoints.current}/${characterData.hitPoints.max}</div>
                </div>
            </div>
        `;
    }
    
    // Add spellcasting information
    if (characterData.spellcasting && ['wizard', 'bard', 'cleric'].includes(characterData.class)) {
        html += `
            <div class="spellcasting-display mb-3">
                <h5>Spellcasting</h5>
                <div class="spellcasting-info small">
                    <div><strong>Ability:</strong> ${characterData.spellcasting.ability.charAt(0).toUpperCase() + characterData.spellcasting.ability.slice(1)}</div>
                    <div><strong>Save DC:</strong> ${characterData.spellcasting.spellSaveDC}</div>
                    <div><strong>Attack:</strong> ${characterData.spellcasting.spellAttackBonus >= 0 ? '+' : ''}${characterData.spellcasting.spellAttackBonus}</div>
                </div>
                
                <!-- Cantrips -->
                ${characterData.spellcasting.cantripsKnown && characterData.spellcasting.cantripsKnown.length > 0 ? `
                    <div class="spell-section mt-2">
                        <span class="spell-type">Cantrips:</span>
                        <span class="spell-list">
                            ${characterData.spellcasting.cantripsKnown.map(id => {
                                const spell = getSpellById(id);
                                return spell ? spell.name : id;
                            }).join(', ')}
                        </span>
                    </div>
                ` : ''}
                
                <!-- Known/Prepared Spells -->
                ${(() => {
                    const preparedSpells = characterData.class === 'wizard' ? 
                        (characterData.spellcasting.spellsPrepared || []) : 
                        (characterData.spellcasting.spellsKnown || []);
                    
                    if (preparedSpells.length > 0) {
                        return `
                            <div class="spell-section">
                                <span class="spell-type">${characterData.class === 'wizard' ? 'Prepared' : 'Known'} Spells:</span>
                                <span class="spell-list">
                                    ${preparedSpells.map(id => {
                                        const spell = getSpellById(id);
                                        return spell ? spell.name : id;
                                    }).join(', ')}
                                </span>
                            </div>
                        `;
                    }
                    return '';
                })()}
                
                <!-- Spell Slots -->
                ${characterData.spellcasting.spellSlots ? `
                    <div class="spell-slots mt-2">
                        <div class="slot-item">
                            <span class="slot-level">Level 1:</span>
                            <span class="slot-count">${characterData.spellcasting.spellSlots[1] || 0} slots</span>
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    // Add skills
    if (characterData.skills && characterData.skills.length > 0) {
        html += `
            <h5>Skills</h5>
            <div class="mb-3">
        `;
        
        characterData.skills.forEach(skill => {
            html += `<span class="badge bg-success me-1 mb-1">${skills[skill]?.name || skill}</span> `;
        });
        
        html += `
            </div>
        `;
    }
    
    // Add features
    let featuresHTML = '';
    if (characterData.features) {
        // Get class feature data
        const classFeatureData = classFeatures[characterData.class]?.level1 || { required: [], optional: [] };
        
        // Handle required features
        if (characterData.features.required && characterData.features.required.length > 0) {
            featuresHTML += '<h5>Features</h5><ul class="list-unstyled small">';
            
            characterData.features.required.forEach(featureId => {
                const feature = classFeatureData.required.find(f => f.id === featureId);
                if (feature) {
                    featuresHTML += `<li><span class="text-light">${feature.name}</span>`;
                    
                    // For active features with usage limits, show usage tracking
                    if (feature.type === 'active' && feature.usageLimit) {
                        featuresHTML += ` <span class="badge bg-secondary">${feature.usageLimit}</span>`;
                    }
                    
                    featuresHTML += `</li>`;
                }
            });
            
            featuresHTML += '</ul>';
        }
        
        // Handle optional features
        if (characterData.features.optional && Object.keys(characterData.features.optional).length > 0) {
            if (!featuresHTML.includes('Features')) {
                featuresHTML += '<h5>Features</h5>';
            }
            featuresHTML += '<ul class="list-unstyled small">';
            
            for (const [featureId, choiceId] of Object.entries(characterData.features.optional)) {
                const featureGroup = classFeatureData.optional.find(f => f.id === featureId);
                
                if (featureGroup) {
                    if (featureGroup.choices) {
                        // For single-choice features like Fighting Style
                        const choice = featureGroup.choices.find(c => c.id === choiceId);
                        if (choice) {
                            featuresHTML += `<li><span class="text-success">${choice.name}</span>`;
                            if (choice.benefit) {
                                featuresHTML += ` <small class="text-light">${choice.benefit}</small>`;
                            }
                            featuresHTML += `</li>`;
                        }
                    } else if (Array.isArray(choiceId)) {
                        // For multi-selection features like Expertise
                        const skillNames = choiceId.map(skillId => skills[skillId]?.name).filter(Boolean);
                        featuresHTML += `<li><span class="text-success">${featureGroup.name}:</span> <small>${skillNames.join(', ')}</small></li>`;
                    }
                }
            }
            
            featuresHTML += '</ul>';
        }
    }
    
    html += `
    <div class="character-features mb-3">
        ${featuresHTML}
    </div>
    `;
    
    // Add description if available
    if (characterData.description) {
        html += `
            <h5 class="mt-3">Description</h5>
            <p class="small">${characterData.description}</p>
        `;
    }
    
    characterSheet.innerHTML = html;
}

// Add a function to generate racial features HTML
function generateRacialFeaturesHTML() {
    if (!characterData.race || !raceData[characterData.race]) {
        return '<p class="text-light">No race selected.</p>';
    }
    
    const race = characterData.race;
    const raceInfo = raceData[race];
    let racialFeaturesHTML = '<div class="row">';
    
    // Add base race features
    racialFeaturesHTML += `
        <div class="col-md-4 mb-3">
            <div class="selection-card">
                <div class="card-body">
                    <h5 class="card-title">${raceInfo.name} Traits</h5>
                    <p class="card-text small">${raceInfo.description}</p>
                    <div class="small">
                        <div><strong>Ability Bonuses:</strong> ${
                            raceInfo.abilityScoreIncrease.all ? 
                            `+${raceInfo.abilityScoreIncrease.all} to all abilities` : 
                            Object.entries(raceInfo.abilityScoreIncrease)
                                .map(([ability, bonus]) => `+${bonus} ${ability.charAt(0).toUpperCase() + ability.slice(1)}`)
                                .join(', ')
                        }</div>
                        <div class="mt-2">
                            <strong>Racial Traits:</strong>
                            <ul class="mb-0 ps-3 mt-1">
                                ${raceInfo.traits.map(trait => `<li>${trait}</li>`).join('')}
                            </ul>
                        </div>
                    </div>
                </div>
                <div class="card-footer">
                    <div class="feature-type-indicator">
                        <i class="bi bi-people-fill"></i> Base Race
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Add sub-race features if applicable
    if (characterData.subrace && characterData.subrace !== 'none' && raceInfo.hasSubraces) {
        const subrace = raceInfo.subraces.find(sr => sr.id === characterData.subrace);
        
        if (subrace) {
            racialFeaturesHTML += `
                <div class="col-md-4 mb-3">
                    <div class="selection-card">
                        <div class="card-body">
                            <h5 class="card-title">${subrace.name} Traits</h5>
                            <p class="card-text small">${subrace.description}</p>
                            <div class="small">
                                <div><strong>Ability Bonuses:</strong> ${
                                    Object.entries(subrace.abilityScoreIncrease)
                                        .map(([ability, bonus]) => `+${bonus} ${ability.charAt(0).toUpperCase() + ability.slice(1)}`)
                                        .join(', ')
                                }</div>
                                <div class="mt-2">
                                    <strong>Additional Traits:</strong>
                                    <ul class="mb-0 ps-3 mt-1">
                                        ${subrace.traits.map(trait => `<li>${trait}</li>`).join('')}
                                    </ul>
                                </div>
                            </div>
                        </div>
                        <div class="card-footer">
                            <div class="feature-type-indicator">
                                <i class="bi bi-person-fill"></i> Sub-Race
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }
    }
    
    racialFeaturesHTML += '</div>';
    return racialFeaturesHTML;
}

// Function to get a readable summary of character features
function getFeaturesSummary(characterData) {
    if (!characterData.features) return '';
    
    const classFeatureData = classFeatures[characterData.class]?.level1 || { required: [], optional: [] };
    let summary = '';
    
    // Add required features
    if (characterData.features.required && characterData.features.required.length > 0) {
        summary += ' I have the following class features: ';
        
        const featureNames = characterData.features.required.map(featureId => {
            const feature = classFeatureData.required.find(f => f.id === featureId);
            return feature ? feature.name : '';
        }).filter(Boolean);
        
        summary += featureNames.join(', ') + '.';
    }
    
    // Add optional features
    if (characterData.features.optional && Object.keys(characterData.features.optional).length > 0) {
        summary += ' I\'ve chosen ';
        
        const choiceSummaries = [];
        
        for (const [featureId, choiceId] of Object.entries(characterData.features.optional)) {
            const featureGroup = classFeatureData.optional.find(f => f.id === featureId);
            
            if (featureGroup) {
                if (featureGroup.choices) {
                    // For single-choice features like Fighting Style
                    const choice = featureGroup.choices.find(c => c.id === choiceId);
                    if (choice) {
                        choiceSummaries.push(`the ${choice.name} ${featureGroup.name.toLowerCase()}`);
                    }
                } else if (Array.isArray(choiceId)) {
                    // For multi-selection features like Expertise
                    const skillNames = choiceId.map(skillId => skills[skillId]?.name).filter(Boolean);
                    if (skillNames.length > 0) {
                        choiceSummaries.push(`${featureGroup.name} in ${skillNames.join(' and ')}`);
                    }
                }
            }
        }
        
        if (choiceSummaries.length > 0) {
            summary += choiceSummaries.join(', ') + '.';
        }
    }
    
    return summary;
}

// Function to send the initial message to the AI with the full character data
function sendInitialMessageToAI(characterData) {
    // Show "typing" indicator
    const chatWindow = document.getElementById('chatWindow');
    const typingDiv = document.createElement('div');
    typingDiv.classList.add('message', 'dm-message', 'typing-indicator');
    typingDiv.innerHTML = '<p>The DM is preparing your adventure...</p>';
    chatWindow.appendChild(typingDiv);
    
    // Scroll to make typing indicator visible
    chatWindow.scrollTop = chatWindow.scrollHeight;
    
    // Get a detailed character introduction for the AI
    const introMessage = getCharacterIntroForAI();
    
    // Prepare the data to send
    const data = {
        message: introMessage,
        character_data: characterData,
        session_id: null  // New session
    };
    
    // Send the API request
    fetch('/api/send-message', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        console.log('Received AI response for new adventure:', data);
        
        // Remove typing indicator
        try {
            chatWindow.removeChild(typingDiv);
        } catch (e) {
            console.log('Could not remove typing indicator', e);
        }
        
        // Add AI response to chat
        const responseDiv = document.createElement('div');
        responseDiv.classList.add('message', 'dm-message');
        responseDiv.innerHTML = `<p>${data.response}</p>`;
        chatWindow.appendChild(responseDiv);
        
        // Scroll to bottom of chat
        chatWindow.scrollTop = chatWindow.scrollHeight;
        
        // Save session ID for future messages
        if (data.session_id) {
            window.sessionId = data.session_id;
            console.log('New adventure session created with ID:', data.session_id);
        }
        
        // Update game state if provided
        if (data.game_state) {
            window.gameState = data.game_state;
            console.log('Game state set to:', data.game_state);
            
            // Update UI based on game state if a function exists
            if (typeof updateUIForGameState === 'function') {
                updateUIForGameState(data.game_state);
            }
        }
    })
    .catch(error => {
        console.error('Error starting adventure with AI:', error);
        
        // Remove typing indicator
        try {
            chatWindow.removeChild(typingDiv);
        } catch (e) {
            console.log('Could not remove typing indicator', e);
        }
        
        // Add error message
        const errorDiv = document.createElement('div');
        errorDiv.classList.add('message', 'dm-message');
        errorDiv.innerHTML = `
            <p>There was a problem starting your adventure. The Dungeon Master seems to be taking a short break. 
            Please try again in a moment. (Error: ${error.message})</p>
        `;
        chatWindow.appendChild(errorDiv);
        
        // Scroll to bottom of chat
        chatWindow.scrollTop = chatWindow.scrollHeight;
    });
}




// Initialize the character creation process when "New Game" is clicked
document.addEventListener('DOMContentLoaded', function() {
    const newGameBtn = document.getElementById('new-game-btn');
    if (newGameBtn) {
        newGameBtn.addEventListener('click', startCharacterCreation);
    }
});

