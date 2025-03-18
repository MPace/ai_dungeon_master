/**
 * Core spell data structure for D&D 5e
 * This contains the basic information needed for all spells in the game
 */

// Define the schools of magic as constants for consistency
const SCHOOLS = {
    ABJURATION: 'Abjuration',
    CONJURATION: 'Conjuration',
    DIVINATION: 'Divination',
    ENCHANTMENT: 'Enchantment',
    EVOCATION: 'Evocation',
    ILLUSION: 'Illusion',
    NECROMANCY: 'Necromancy',
    TRANSMUTATION: 'Transmutation'
};

// Define the classes that can use spells
const SPELL_CLASSES = {
    BARD: 'bard',
    CLERIC: 'cleric',
    DRUID: 'druid',
    PALADIN: 'paladin',
    RANGER: 'ranger',
    SORCERER: 'sorcerer',
    WARLOCK: 'warlock',
    WIZARD: 'wizard'
};

// Main spell database
const spellData = {
    // Cantrips (Level 0)
    'acid-splash': {
        id: 'acid-splash',
        name: 'Acid Splash',
        level: 0,
        school: SCHOOLS.CONJURATION,
        castingTime: '1 action',
        range: '60 feet',
        components: ['V', 'S'],
        materials: null,
        duration: 'Instantaneous',
        concentration: false,
        ritual: false,
        description: 'You hurl a bubble of acid. Choose one creature you can see within range, or choose two creatures you can see within range that are within 5 feet of each other. A target must succeed on a Dexterity saving throw or take 1d6 acid damage.\n\nThis spell\'s damage increases by 1d6 when you reach 5th level (2d6), 11th level (3d6), and 17th level (4d6).',
        higherLevels: null,
        savingThrow: 'Dexterity',
        damageType: 'Acid',
        classes: [SPELL_CLASSES.SORCERER, SPELL_CLASSES.WIZARD]
    },
    
    'dancing-lights': {
        id: 'dancing-lights',
        name: 'Dancing Lights',
        level: 0,
        school: SCHOOLS.EVOCATION,
        castingTime: '1 action',
        range: '120 feet',
        components: ['V', 'S', 'M'],
        materials: 'A bit of phosphorus or wychwood, or a glowworm',
        duration: 'Concentration, up to 1 minute',
        concentration: true,
        ritual: false,
        description: 'You create up to four torch-sized lights within range, making them appear as torches, lanterns, or glowing orbs that hover in the air for the duration. You can also combine the four lights into one glowing vaguely humanoid form of Medium size. Whichever form you choose, each light sheds dim light in a 10-foot radius.\n\nAs a bonus action on your turn, you can move the lights up to 60 feet to a new spot within range. A light must be within 20 feet of another light created by this spell, and a light winks out if it exceeds the spell\'s range.',
        higherLevels: null,
        savingThrow: null,
        damageType: null,
        classes: [SPELL_CLASSES.BARD, SPELL_CLASSES.SORCERER, SPELL_CLASSES.WIZARD]
    },
    
    'fire-bolt': {
        id: 'fire-bolt',
        name: 'Fire Bolt',
        level: 0,
        school: SCHOOLS.EVOCATION,
        castingTime: '1 action',
        range: '120 feet',
        components: ['V', 'S'],
        materials: null,
        duration: 'Instantaneous',
        concentration: false,
        ritual: false,
        description: 'You hurl a mote of fire at a creature or object within range. Make a ranged spell attack against the target. On a hit, the target takes 1d10 fire damage. A flammable object hit by this spell ignites if it isn\'t being worn or carried.\n\nThis spell\'s damage increases by 1d10 when you reach 5th level (2d10), 11th level (3d10), and 17th level (4d10).',
        higherLevels: null,
        attackType: 'Ranged Spell Attack',
        damageType: 'Fire',
        classes: [SPELL_CLASSES.SORCERER, SPELL_CLASSES.WIZARD]
    },
    
    'light': {
        id: 'light',
        name: 'Light',
        level: 0,
        school: SCHOOLS.EVOCATION,
        castingTime: '1 action',
        range: 'Touch',
        components: ['V', 'M'],
        materials: 'A firefly or phosphorescent moss',
        duration: '1 hour',
        concentration: false,
        ritual: false,
        description: 'You touch one object that is no larger than 10 feet in any dimension. Until the spell ends, the object sheds bright light in a 20-foot radius and dim light for an additional 20 feet. The light can be colored as you like. Completely covering the object with something opaque blocks the light. The spell ends if you cast it again or dismiss it as an action.\n\nIf you target an object held or worn by a hostile creature, that creature must succeed on a Dexterity saving throw to avoid the spell.',
        higherLevels: null,
        savingThrow: 'Dexterity',
        damageType: null,
        classes: [SPELL_CLASSES.BARD, SPELL_CLASSES.CLERIC, SPELL_CLASSES.SORCERER, SPELL_CLASSES.WIZARD]
    },
    
    'mage-hand': {
        id: 'mage-hand',
        name: 'Mage Hand',
        level: 0,
        school: SCHOOLS.CONJURATION,
        castingTime: '1 action',
        range: '30 feet',
        components: ['V', 'S'],
        materials: null,
        duration: '1 minute',
        concentration: false,
        ritual: false,
        description: 'A spectral, floating hand appears at a point you choose within range. The hand lasts for the duration or until you dismiss it as an action. The hand vanishes if it is ever more than 30 feet away from you or if you cast this spell again.\n\nYou can use your action to control the hand. You can use the hand to manipulate an object, open an unlocked door or container, stow or retrieve an item from an open container, or pour the contents out of a vial. You can move the hand up to 30 feet each time you use it.\n\nThe hand can\'t attack, activate magical items, or carry more than 10 pounds.',
        higherLevels: null,
        savingThrow: null,
        damageType: null,
        classes: [SPELL_CLASSES.BARD, SPELL_CLASSES.SORCERER, SPELL_CLASSES.WARLOCK, SPELL_CLASSES.WIZARD]
    },
    
    'prestidigitation': {
        id: 'prestidigitation',
        name: 'Prestidigitation',
        level: 0,
        school: SCHOOLS.TRANSMUTATION,
        castingTime: '1 action',
        range: '10 feet',
        components: ['V', 'S'],
        materials: null,
        duration: '1 hour',
        concentration: false,
        ritual: false,
        description: 'This spell is a minor magical trick that novice spellcasters use for practice. You create one of the following magical effects within range:\n\n• You create an instantaneous, harmless sensory effect, such as a shower of sparks, a puff of wind, faint musical notes, or an odd odor.\n• You instantaneously light or snuff out a candle, a torch, or a small campfire.\n• You instantaneously clean or soil an object no larger than 1 cubic foot.\n• You chill, warm, or flavor up to 1 cubic foot of nonliving material for 1 hour.\n• You make a color, a small mark, or a symbol appear on an object or a surface for 1 hour.\n• You create a nonmagical trinket or an illusory image that can fit in your hand and that lasts until the end of your next turn.\n\nIf you cast this spell multiple times, you can have up to three of its non-instantaneous effects active at a time, and you can dismiss such an effect as an action.',
        higherLevels: null,
        savingThrow: null,
        damageType: null,
        classes: [SPELL_CLASSES.BARD, SPELL_CLASSES.SORCERER, SPELL_CLASSES.WARLOCK, SPELL_CLASSES.WIZARD]
    },
    
    'sacred-flame': {
        id: 'sacred-flame',
        name: 'Sacred Flame',
        level: 0,
        school: SCHOOLS.EVOCATION,
        castingTime: '1 action',
        range: '60 feet',
        components: ['V', 'S'],
        materials: null,
        duration: 'Instantaneous',
        concentration: false,
        ritual: false,
        description: 'Flame-like radiance descends on a creature that you can see within range. The target must succeed on a Dexterity saving throw or take 1d8 radiant damage. The target gains no benefit from cover for this saving throw.\n\nThe spell\'s damage increases by 1d8 when you reach 5th level (2d8), 11th level (3d8), and 17th level (4d8).',
        higherLevels: null,
        savingThrow: 'Dexterity',
        damageType: 'Radiant',
        classes: [SPELL_CLASSES.CLERIC]
    },
    
    'thaumaturgy': {
        id: 'thaumaturgy',
        name: 'Thaumaturgy',
        level: 0,
        school: SCHOOLS.TRANSMUTATION,
        castingTime: '1 action',
        range: '30 feet',
        components: ['V'],
        materials: null,
        duration: '1 minute',
        concentration: false,
        ritual: false,
        description: 'You manifest a minor wonder, a sign of supernatural power, within range. You create one of the following magical effects within range:\n\n• Your voice booms up to three times as loud as normal for 1 minute.\n• You cause flames to flicker, brighten, dim, or change color for 1 minute.\n• You cause harmless tremors in the ground for 1 minute.\n• You create an instantaneous sound that originates from a point of your choice within range, such as a rumble of thunder, the cry of a raven, or ominous whispers.\n• You instantaneously cause an unlocked door or window to fly open or slam shut.\n• You alter the appearance of your eyes for 1 minute.\n\nIf you cast this spell multiple times, you can have up to three of its 1-minute effects active at a time, and you can dismiss such an effect as an action.',
        higherLevels: null,
        savingThrow: null,
        damageType: null,
        classes: [SPELL_CLASSES.CLERIC]
    },
    
    // 1st Level Spells
    'burning-hands': {
        id: 'burning-hands',
        name: 'Burning Hands',
        level: 1,
        school: SCHOOLS.EVOCATION,
        castingTime: '1 action',
        range: 'Self (15-foot cone)',
        components: ['V', 'S'],
        materials: null,
        duration: 'Instantaneous',
        concentration: false,
        ritual: false,
        description: 'As you hold your hands with thumbs touching and fingers spread, a thin sheet of flames shoots forth from your outstretched fingertips. Each creature in a 15-foot cone must make a Dexterity saving throw. A creature takes 3d6 fire damage on a failed save, or half as much damage on a successful one.\n\nThe fire ignites any flammable objects in the area that aren\'t being worn or carried.',
        higherLevels: 'When you cast this spell using a spell slot of 2nd level or higher, the damage increases by 1d6 for each slot level above 1st.',
        savingThrow: 'Dexterity',
        damageType: 'Fire',
        classes: [SPELL_CLASSES.SORCERER, SPELL_CLASSES.WIZARD]
    },
    
    'cure-wounds': {
        id: 'cure-wounds',
        name: 'Cure Wounds',
        level: 1,
        school: SCHOOLS.EVOCATION,
        castingTime: '1 action',
        range: 'Touch',
        components: ['V', 'S'],
        materials: null,
        duration: 'Instantaneous',
        concentration: false,
        ritual: false,
        description: 'A creature you touch regains a number of hit points equal to 1d8 + your spellcasting ability modifier. This spell has no effect on undead or constructs.',
        higherLevels: 'When you cast this spell using a spell slot of 2nd level or higher, the healing increases by 1d8 for each slot level above 1st.',
        savingThrow: null,
        damageType: null,
        healing: true,
        classes: [SPELL_CLASSES.BARD, SPELL_CLASSES.CLERIC, SPELL_CLASSES.DRUID, SPELL_CLASSES.PALADIN, SPELL_CLASSES.RANGER]
    },
    
    'detect-magic': {
        id: 'detect-magic',
        name: 'Detect Magic',
        level: 1,
        school: SCHOOLS.DIVINATION,
        castingTime: '1 action',
        range: 'Self',
        components: ['V', 'S'],
        materials: null,
        duration: 'Concentration, up to 10 minutes',
        concentration: true,
        ritual: true,
        description: 'For the duration, you sense the presence of magic within 30 feet of you. If you sense magic in this way, you can use your action to see a faint aura around any visible creature or object in the area that bears magic, and you learn its school of magic, if any.\n\nThe spell can penetrate most barriers, but it is blocked by 1 foot of stone, 1 inch of common metal, a thin sheet of lead, or 3 feet of wood or dirt.',
        higherLevels: null,
        savingThrow: null,
        damageType: null,
        classes: [SPELL_CLASSES.BARD, SPELL_CLASSES.CLERIC, SPELL_CLASSES.DRUID, SPELL_CLASSES.PALADIN, SPELL_CLASSES.RANGER, SPELL_CLASSES.SORCERER, SPELL_CLASSES.WIZARD]
    },
    
    'magic-missile': {
        id: 'magic-missile',
        name: 'Magic Missile',
        level: 1,
        school: SCHOOLS.EVOCATION,
        castingTime: '1 action',
        range: '120 feet',
        components: ['V', 'S'],
        materials: null,
        duration: 'Instantaneous',
        concentration: false,
        ritual: false,
        description: 'You create three glowing darts of magical force. Each dart hits a creature of your choice that you can see within range. A dart deals 1d4 + 1 force damage to its target. The darts all strike simultaneously, and you can direct them to hit one creature or several.',
        higherLevels: 'When you cast this spell using a spell slot of 2nd level or higher, the spell creates one more dart for each slot level above 1st.',
        savingThrow: null,
        damageType: 'Force',
        classes: [SPELL_CLASSES.SORCERER, SPELL_CLASSES.WIZARD]
    },
    
    'shield': {
        id: 'shield',
        name: 'Shield',
        level: 1,
        school: SCHOOLS.ABJURATION,
        castingTime: '1 reaction, which you take when you are hit by an attack or targeted by the magic missile spell',
        range: 'Self',
        components: ['V', 'S'],
        materials: null,
        duration: '1 round',
        concentration: false,
        ritual: false,
        description: 'An invisible barrier of magical force appears and protects you. Until the start of your next turn, you have a +5 bonus to AC, including against the triggering attack, and you take no damage from magic missile.',
        higherLevels: null,
        savingThrow: null,
        damageType: null,
        classes: [SPELL_CLASSES.SORCERER, SPELL_CLASSES.WIZARD]
    },
    
    'sleep': {
        id: 'sleep',
        name: 'Sleep',
        level: 1,
        school: SCHOOLS.ENCHANTMENT,
        castingTime: '1 action',
        range: '90 feet',
        components: ['V', 'S', 'M'],
        materials: 'A pinch of fine sand, rose petals, or a cricket',
        duration: '1 minute',
        concentration: false,
        ritual: false,
        description: 'This spell sends creatures into a magical slumber. Roll 5d8; the total is how many hit points of creatures this spell can affect. Creatures within 20 feet of a point you choose within range are affected in ascending order of their current hit points (ignoring unconscious creatures).\n\nStarting with the creature that has the lowest current hit points, each creature affected by this spell falls unconscious until the spell ends, the sleeper takes damage, or someone uses an action to shake or slap the sleeper awake. Subtract each creature\'s hit points from the total before moving on to the creature with the next lowest hit points. A creature\'s hit points must be equal to or less than the remaining total for that creature to be affected.\n\nUndead and creatures immune to being charmed aren\'t affected by this spell.',
        higherLevels: 'When you cast this spell using a spell slot of 2nd level or higher, roll an additional 2d8 for each slot level above 1st.',
        savingThrow: null,
        damageType: null,
        classes: [SPELL_CLASSES.BARD, SPELL_CLASSES.SORCERER, SPELL_CLASSES.WIZARD]
    },

    'color spray': {
        id: 'color-spray',
        name: 'Color Spray',
        level: 1,
        school: SCHOOLS.ILLUSION,
        castingTime: '1 action',
        range: 'Self (15-foot cone)',
        components: ['V', 'S', 'M'],
        materials: 'A pinch of powder or sand that is colored red, yellow, and blue',
        duration: '1 round',
        concentration: false,
        ritual: false,
        description: 'A dazzling array of flashing, colored light springs from your hand. Roll 6d10; the total is how many hit points of creatures this spell can affect. Creatures in a 15-foot cone originating from you are affected in ascending order of their current hit points (ignoring unconscious creatures and creatures that can\'t see).\n\nStarting with the creature that has the lowest current hit points, each creature affected by this spell is blinded until the spell ends. Subtract each creature\'s hit points from the total before moving on to the creature with the next lowest hit points.\n\nA creature\'s hit points must be equal to or less than the remaining total for that creature to be affected.',
        higherLevels: 'When you cast this spell using a spell slot of 2nd level or higher, roll an additional 2d10 for each slot level above 1st.',
        savingThrow: null,
        damageType: null,
        classes: [SPELL_CLASSES.SORCERER, SPELL_CLASSES.WIZARD]
    },
    
    // 2nd Level Spells
    'hold-person': {
        id: 'hold-person',
        name: 'Hold Person',
        level: 2,
        school: SCHOOLS.ENCHANTMENT,
        castingTime: '1 action',
        range: '60 feet',
        components: ['V', 'S', 'M'],
        materials: 'A small, straight piece of iron',
        duration: 'Concentration, up to 1 minute',
        concentration: true,
        ritual: false,
        description: 'Choose a humanoid that you can see within range. The target must succeed on a Wisdom saving throw or be paralyzed for the duration. At the end of each of its turns, the target can make another Wisdom saving throw. On a success, the spell ends on the target.',
        higherLevels: 'When you cast this spell using a spell slot of 3rd level or higher, you can target one additional humanoid for each slot level above 2nd. The humanoids must be within 30 feet of each other when you target them.',
        savingThrow: 'Wisdom',
        damageType: null,
        classes: [SPELL_CLASSES.BARD, SPELL_CLASSES.CLERIC, SPELL_CLASSES.DRUID, SPELL_CLASSES.SORCERER, SPELL_CLASSES.WARLOCK, SPELL_CLASSES.WIZARD]
    },
    
    'invisibility': {
        id: 'invisibility',
        name: 'Invisibility',
        level: 2,
        school: SCHOOLS.ILLUSION,
        castingTime: '1 action',
        range: 'Touch',
        components: ['V', 'S', 'M'],
        materials: 'An eyelash encased in gum arabic',
        duration: 'Concentration, up to 1 hour',
        concentration: true,
        ritual: false,
        description: 'A creature you touch becomes invisible until the spell ends. Anything the target is wearing or carrying is invisible as long as it is on the target\'s person. The spell ends for a target that attacks or casts a spell.',
        higherLevels: 'When you cast this spell using a spell slot of 3rd level or higher, you can target one additional creature for each slot level above 2nd.',
        savingThrow: null,
        damageType: null,
        classes: [SPELL_CLASSES.BARD, SPELL_CLASSES.SORCERER, SPELL_CLASSES.WARLOCK, SPELL_CLASSES.WIZARD]
    },
    
    'scorching-ray': {
        id: 'scorching-ray',
        name: 'Scorching Ray',
        level: 2,
        school: SCHOOLS.EVOCATION,
        castingTime: '1 action',
        range: '120 feet',
        components: ['V', 'S'],
        materials: null,
        duration: 'Instantaneous',
        concentration: false,
        ritual: false,
        description: 'You create three rays of fire and hurl them at targets within range. You can hurl them at one target or several.\n\nMake a ranged spell attack for each ray. On a hit, the target takes 2d6 fire damage.',
        higherLevels: 'When you cast this spell using a spell slot of 3rd level or higher, you create one additional ray for each slot level above 2nd.',
        attackType: 'Ranged Spell Attack',
        damageType: 'Fire',
        classes: [SPELL_CLASSES.SORCERER, SPELL_CLASSES.WIZARD]
    },
    
    // 3rd Level Spells
    'fireball': {
        id: 'fireball',
        name: 'Fireball',
        level: 3,
        school: SCHOOLS.EVOCATION,
        castingTime: '1 action',
        range: '150 feet',
        components: ['V', 'S', 'M'],
        materials: 'A tiny ball of bat guano and sulfur',
        duration: 'Instantaneous',
        concentration: false,
        ritual: false,
        description: 'A bright streak flashes from your pointing finger to a point you choose within range and then blossoms with a low roar into an explosion of flame. Each creature in a 20-foot-radius sphere centered on that point must make a Dexterity saving throw. A target takes 8d6 fire damage on a failed save, or half as much damage on a successful one.\n\nThe fire spreads around corners. It ignites flammable objects in the area that aren\'t being worn or carried.',
        higherLevels: 'When you cast this spell using a spell slot of 4th level or higher, the damage increases by 1d6 for each slot level above 3rd.',
        savingThrow: 'Dexterity',
        damageType: 'Fire',
        classes: [SPELL_CLASSES.SORCERER, SPELL_CLASSES.WIZARD]
    }
    
    // Add more spells as needed
};

// Helper functions

/**
 * Get all available cantrips for a specific class
 * @param {string} className - The class name to filter by
 * @returns {Array} - Array of cantrip objects
 */
function getCantripsForClass(className) {
    return Object.values(spellData).filter(spell => 
        spell.level === 0 && spell.classes.includes(className)
    );
}

/**
 * Get all available spells of a specific level for a class
 * @param {string} className - The class name to filter by
 * @param {number} level - The spell level (1-9)
 * @returns {Array} - Array of spell objects
 */
function getSpellsForClassAndLevel(className, level) {
    return Object.values(spellData).filter(spell => 
        spell.level === level && spell.classes.includes(className)
    );
}

/**
 * Get a specific spell by ID
 * @param {string} spellId - The spell ID to find
 * @returns {Object|null} - The spell object or null if not found
 */
function getSpellById(spellId) {
    return spellData[spellId] || null;
}

// Export the data and helper functions

window.spellData = spellData;
window.getCantripsForClass = getCantripsForClass;
window.getSpellsForClassAndLevel = getSpellsForClassAndLevel;
window.getSpellById = getSpellById;
