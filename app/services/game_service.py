"""
Enhanced Game Service with Memory Management
"""
from app.models.game_session import GameSession
from app.services.character_service import CharacterService
from app.extensions import get_db
from datetime import datetime
import uuid
import logging
import random
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class GameService:
    """Service for handling game session operations with memory management"""
    
    @staticmethod
    def create_session(character_id, user_id):
        """
        Create a new game session
        
        Args:
            character_id (str): Character ID
            user_id (str): User ID
            
        Returns:
            dict: Result with success status and session
        """
        try:
            # Get character data to verify ownership
            character = CharacterService.get_character(character_id, user_id)
            if character is None:
                logger.error(f"Character not found for session creation: {character_id}")
                return {'success': False, 'error': 'Character not found'}
            
            # Create a new session object
            session_id = str(uuid.uuid4())
            
            # Create a new GameSession object
            game_session = GameSession(
                session_id=session_id,
                character_id=character_id,
                user_id=user_id,
                game_state='intro',
                history=[],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                # Initialize memory-related fields
                pinned_memories=[],
                session_summary="Session beginning. No summary yet.",
                important_entities={},
                player_decisions=[]
            )
            
            # Save session to database
            db = get_db()
            if db is None:
                logger.error("Database connection failed when creating session")
                return {'success': False, 'error': 'Database connection error'}
            
            # Convert GameSession to dictionary for storage
            session_dict = game_session.to_dict()
            
            # Insert into database
            result = db.sessions.insert_one(session_dict)
            
            if result.inserted_id:
                logger.info(f"Game session created: {session_id}")
                
                # Update character's last_played timestamp
                db.characters.update_one(
                    {'character_id': character_id},
                    {'$set': {'last_played': datetime.utcnow()}}
                )
                
                # Initialize memory service for this session
                GameService._initialize_session_memory(session_id, character_id, user_id)
                
                return {'success': True, 'session': game_session}
            else:
                logger.error(f"Failed to create game session")
                return {'success': False, 'error': 'Failed to create game session'}
                
        except Exception as e:
            logger.error(f"Error creating game session: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_session(session_id, user_id=None):
        """
        Get a game session by ID
        
        Args:
            session_id (str): Session ID
            user_id (str, optional): User ID for permission check
            
        Returns:
            dict: Result with success status and session
        """
        try:
            db = get_db()
            if db is None:
                logger.error("Database connection failed when getting session")
                return {'success': False, 'error': 'Database connection error'}
            
            # Build query
            query = {'session_id': session_id}
            if user_id:
                query['user_id'] = user_id
            
            # Find session
            session_data = db.sessions.find_one(query)
            
            if not session_data:
                logger.warning(f"Session not found: {session_id}")
                return {'success': False, 'error': 'Session not found'}
            
            session = GameSession.from_dict(session_data)
            return {'success': True, 'session': session}
            
        except Exception as e:
            logger.error(f"Error getting session: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def send_message(session_id, message, user_id):
        """
        Send a message in a game session
        
        Args:
            session_id (str): Session ID or None if starting fresh
            message (str): User message
            user_id (str): User ID
            
        Returns:
            dict: Result with success status and AI response
        """
        # Import here to avoid circular import
        from app.services.ai_service import AIService
        from app.services.memory_service_enhanced import EnhancedMemoryService

        memory_service = EnhancedMemoryService()
        ai_service = AIService()
        
        try:
            # Step 1: Get or create a session
            session = None
            character = None
            is_new_session = False
            
            if session_id:
                # Try to get existing session
                session_result = GameService.get_session(session_id, user_id)
                if session_result.get('success', False):
                    session = session_result['session']
                    logger.info(f"Using existing session: {session_id}")
                else:
                    logger.warning(f"Session not found: {session_id}, will create new session")
                    session_id = None  # Force creation of new session
            
            if not session:
                # Create a new session
                logger.info("Creating new session")
                is_new_session = True
                
                # Get character to use
                characters_result = CharacterService.list_characters(user_id)
                if not characters_result.get('success', False) or not characters_result.get('characters'):
                    error_msg = "No characters found. Please create a character first."
                    logger.error(error_msg)
                    return {'success': False, 'error': error_msg}
                
                # Get first character
                characters = characters_result['characters']
                first_character = characters[0]
                
                # Get character_id (handle both object and dict formats)
                if hasattr(first_character, 'character_id'):
                    character_id = first_character.character_id
                else:
                    character_id = first_character.get('character_id')
                    
                if not character_id:
                    return {'success': False, 'error': 'Invalid character data'}
                    
                # Create session
                logger.info(f"Creating session with character ID: {character_id}")
                session_result = GameService.create_session(character_id, user_id)
                
                if not session_result.get('success', False):
                    return session_result
                    
                session = session_result['session']
                logger.info(f"Created new session: {session.session_id}")
            
            # Step 2: Get character data
            character_result = CharacterService.get_character(session.character_id, user_id)
            if not character_result or not character_result.get('success', False):
                error_msg = "Failed to retrieve character data"
                logger.error(f"{error_msg}: {character_result.get('error') if character_result else 'Unknown error'}")
                return {'success': False, 'error': error_msg}
                
            character = character_result.get('character')
            
            # Step 3: Add player message to session history
            session.add_message('player', message)
            
            # Step 4: Store player message in memory system
            memory_service.store_memory_with_text(
                content=message,
                memory_type='short_term',
                session_id=session.session_id,
                character_id=character.character_id,
                user_id=user_id,
                importance=GameService._calculate_message_importance(message),
                metadata={'sender': 'player'}
            )
            
            # Step 5: Process message for entities
            GameService._process_message_for_entities(session, message)
            
            # Step 6: Generate AI response
            ai_response = ai_service.generate_response(
                message, 
                session.history, 
                character, 
                session.game_state
            )
            
            # Step 7: Add AI response to session history
            session.add_message('dm', ai_response.response_text)
            
            # Step 8: Process AI response for entities
            GameService._process_message_for_entities(session, ai_response.response_text, is_dm=True)
            
            # Step 9: Store AI response in memory system
            memory_service.store_memory_with_text(
                content=ai_response.response_text,
                memory_type='short_term',
                session_id=session.session_id,
                character_id=character.character_id,
                user_id=user_id,
                importance=GameService._calculate_message_importance(ai_response.response_text),
                metadata={'sender': 'dm'}
            )
            
            # Step 10: Update game state based on content
            GameService._update_game_state(session, message, ai_response.response_text)
            
            # Step 11: Update session summary if needed
            if not is_new_session:
                GameService._update_session_summary_if_needed(session)
            
            # Step 12: Save session to database
            db = get_db()
            if db is None:
                return {'success': False, 'error': 'Database connection error'}
            
            result = db.sessions.update_one(
                {'session_id': session.session_id},
                {'$set': session.to_dict()}
            )
            
            if not result.acknowledged:
                logger.error(f"Failed to update session: {session.session_id}")
                return {'success': False, 'error': 'Failed to update session'}
            
            # Step 13: Update character's last_played timestamp
            db.characters.update_one(
                {'character_id': session.character_id},
                {'$set': {'last_played': datetime.utcnow()}}
            )
            
            # Step 14: Return successful response
            return {
                'success': True, 
                'response': ai_response.response_text,
                'session_id': session.session_id,
                'game_state': session.game_state,
                'new_session': is_new_session,
                'memory_used': not is_new_session,
                'entities_found': GameService._get_latest_entities(session, 3)
            }
                
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_session_memories(session_id, user_id, limit=20, memory_type='all'):
        """
        Get memories associated with a session
        
        Args:
            session_id (str): Session ID
            user_id (str): User ID for permission check
            limit (int): Maximum number of memories to return
            memory_type (str): Type of memories (all, short_term, long_term, summary)
            
        Returns:
            dict: Result with success status and memories
        """
        try:
            # First check if the user has access to this session
            session_result = GameService.get_session(session_id, user_id)
            if not session_result['success']:
                return {'success': False, 'error': 'Session not found or access denied'}
            
            # Get memory service
            from app.services.memory_service_enhanced import EnhancedMemoryService
            memory_service = EnhancedMemoryService()
            
            db = get_db()
            if db is None:
                return {'success': False, 'error': 'Database connection error'}
            
            # Build query
            query = {'session_id': session_id}
            if memory_type != 'all':
                query['memory_type'] = memory_type
            
            # Sort by created_at descending (newest first)
            memories = list(db.memory_vectors.find(query).sort('created_at', -1).limit(limit))
            
            # Return memories
            return {'success': True, 'memories': memories}
            
        except Exception as e:
            logger.error(f"Error getting session memories: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def pin_memory(session_id, memory_id, user_id, importance=None, note=None):
        """
        Pin a memory to a session
        
        Args:
            session_id (str): Session ID
            memory_id (str): Memory ID to pin
            user_id (str): User ID for permission check
            importance (int, optional): Optional importance override
            note (str, optional): Optional note about why this memory is pinned
            
        Returns:
            dict: Result with success status
        """
        try:
            # Check if the user has access to this session
            session_result = GameService.get_session(session_id, user_id)
            if not session_result['success']:
                return {'success': False, 'error': 'Session not found or access denied'}
            
            session = session_result['session']
            
            # Pin the memory
            session.pin_memory(memory_id, importance, note)
            
            # Save session
            db = get_db()
            if db is None:
                return {'success': False, 'error': 'Database connection error'}
            
            result = db.sessions.update_one(
                {'session_id': session_id},
                {'$set': {'pinned_memories': session.pinned_memories}}
            )
            
            if result.acknowledged:
                return {'success': True, 'message': 'Memory pinned successfully'}
            else:
                return {'success': False, 'error': 'Failed to pin memory'}
                
        except Exception as e:
            logger.error(f"Error pinning memory: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def unpin_memory(session_id, memory_id, user_id):
        """
        Unpin a memory from a session
        
        Args:
            session_id (str): Session ID
            memory_id (str): Memory ID to unpin
            user_id (str): User ID for permission check
            
        Returns:
            dict: Result with success status
        """
        try:
            # Check if the user has access to this session
            session_result = GameService.get_session(session_id, user_id)
            if not session_result['success']:
                return {'success': False, 'error': 'Session not found or access denied'}
            
            session = session_result['session']
            
            # Unpin the memory
            session.unpin_memory(memory_id)
            
            # Save session
            db = get_db()
            if db is None:
                return {'success': False, 'error': 'Database connection error'}
            
            result = db.sessions.update_one(
                {'session_id': session_id},
                {'$set': {'pinned_memories': session.pinned_memories}}
            )
            
            if result.acknowledged:
                return {'success': True, 'message': 'Memory unpinned successfully'}
            else:
                return {'success': False, 'error': 'Failed to unpin memory'}
                
        except Exception as e:
            logger.error(f"Error unpinning memory: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_important_entities(session_id, user_id):
        """
        Get important entities for a session
        
        Args:
            session_id (str): Session ID
            user_id (str): User ID for permission check
            
        Returns:
            dict: Result with success status and entities
        """
        try:
            # Check if the user has access to this session
            session_result = GameService.get_session(session_id, user_id)
            if not session_result['success']:
                return {'success': False, 'error': 'Session not found or access denied'}
            
            session = session_result['session']
            
            # Return entities
            return {
                'success': True, 
                'entities': session.important_entities
            }
                
        except Exception as e:
            logger.error(f"Error getting important entities: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def update_entity(session_id, entity_name, entity_data, user_id):
        """
        Update an entity in a session
        
        Args:
            session_id (str): Session ID
            entity_name (str): Entity name
            entity_data (dict): Updated entity data
            user_id (str): User ID for permission check
            
        Returns:
            dict: Result with success status
        """
        try:
            # Check if the user has access to this session
            session_result = GameService.get_session(session_id, user_id)
            if not session_result['success']:
                return {'success': False, 'error': 'Session not found or access denied'}
            
            session = session_result['session']
            
            # Update the entity
            if entity_name in session.important_entities:
                session.important_entities[entity_name].update(entity_data)
                session.important_entities[entity_name]['updated_at'] = datetime.utcnow().isoformat()
            else:
                return {'success': False, 'error': 'Entity not found'}
            
            # Save session
            db = get_db()
            if db is None:
                return {'success': False, 'error': 'Database connection error'}
            
            result = db.sessions.update_one(
                {'session_id': session_id},
                {'$set': {'important_entities': session.important_entities}}
            )
            
            if result.acknowledged:
                return {'success': True, 'message': 'Entity updated successfully'}
            else:
                return {'success': False, 'error': 'Failed to update entity'}
                
        except Exception as e:
            logger.error(f"Error updating entity: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_session_summary(session_id, user_id):
        """
        Get summary for a session
        
        Args:
            session_id (str): Session ID
            user_id (str): User ID for permission check
            
        Returns:
            dict: Result with success status and summary
        """
        try:
            # Check if the user has access to this session
            session_result = GameService.get_session(session_id, user_id)
            if not session_result['success']:
                return {'success': False, 'error': 'Session not found or access denied'}
            
            session = session_result['session']
            
            # If summary is empty, generate one
            if not session.session_summary or session.session_summary == "Session beginning. No summary yet.":
                GameService._generate_session_summary(session)
                
                # Save session
                db = get_db()
                if db is None:
                    return {'success': False, 'error': 'Database connection error'}
                
                db.sessions.update_one(
                    {'session_id': session_id},
                    {'$set': {'session_summary': session.session_summary}}
                )
            
            # Return summary
            return {
                'success': True, 
                'summary': session.session_summary
            }
                
        except Exception as e:
            logger.error(f"Error getting session summary: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def _update_game_state(session, message, ai_response=None):
        """
        Update game state based on message content
        
        Args:
            session (GameSession): Game session
            message (str): User message
            ai_response (str, optional): AI response text
            
        Returns:
            None
        """
        old_state = session.game_state
        
        # Simple keyword-based state update
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['attack', 'fight', 'hit', 'cast', 'kill', 'slay', 'battle']):
            session.game_state = 'combat'
        elif any(word in message_lower for word in ['talk', 'speak', 'ask', 'say', 'chat', 'convince', 'persuade']):
            session.game_state = 'social'
        elif any(word in message_lower for word in ['look', 'search', 'investigate', 'explore', 'examine', 'find']):
            session.game_state = 'exploration'
        
        # Also check AI response if provided
        if ai_response:
            ai_lower = ai_response.lower()
            
            # Combat indicators in DM response
            if (session.game_state != 'combat' and 
                any(word in ai_lower for word in ['initiative', 'roll for initiative', 'attack roll', 'make an attack'])):
                session.game_state = 'combat'
            
            # Social indicators in DM response
            elif (session.game_state != 'social' and
                  any(word in ai_lower for word in ['persuasion check', 'charisma check', 'deception check'])):
                session.game_state = 'social'
            
            # Exploration indicators in DM response
            elif (session.game_state != 'exploration' and
                  any(word in ai_lower for word in ['perception check', 'investigation check', 'you see', 'you notice'])):
                session.game_state = 'exploration'
        
        if old_state != session.game_state:
            logger.info(f"Game state changed from {old_state} to {session.game_state}")
    
    @staticmethod
    def _initialize_session_memory(session_id, character_id, user_id):
        """
        Initialize memory for a new session
        
        Args:
            session_id (str): Session ID
            character_id (str): Character ID
            user_id (str): User ID
            
        Returns:
            None
        """
        try:
            from app.services.memory_service_enhanced import EnhancedMemoryService
            memory_service = EnhancedMemoryService()
            
            # Get character data
            character_result = CharacterService.get_character(character_id, user_id)
            if character_result is None:
                logger.error(f"Character not found for memory initialization: {character_id}")
                return
            
            character = character_result
            
            # Create initial memory entry with character info
            character_info = f"Character: {character.name}. A level {character.level} {character.race} {character.character_class}."
            if character.description:
                character_info += f" Description: {character.description}"
            
            memory_service.store_memory_with_text(
                content=character_info,
                memory_type='long_term',  # Store as long-term memory
                session_id=session_id,
                character_id=character_id,
                user_id=user_id,
                importance=10,  # Highest importance
                metadata={'type': 'character_info', 'persistent': True}
            )
            
            # Store any character abilities, skills, or features as semantic memories
            if character.abilities:
                abilities_text = "Character abilities: "
                for ability, score in character.abilities.items():
                    modifier = (score - 10) // 2
                    sign = "+" if modifier >= 0 else ""
                    abilities_text += f"{ability.capitalize()}: {score} ({sign}{modifier}). "
                
                memory_service.store_memory_with_text(
                    content=abilities_text,
                    memory_type='semantic',
                    session_id=session_id,
                    character_id=character_id,
                    user_id=user_id,
                    importance=8,
                    metadata={'type': 'abilities', 'persistent': True}
                )
            
            if character.skills and len(character.skills) > 0:
                skills_text = f"Character is proficient in: {', '.join(character.skills)}."
                
                memory_service.store_memory_with_text(
                    content=skills_text,
                    memory_type='semantic',
                    session_id=session_id,
                    character_id=character_id,
                    user_id=user_id,
                    importance=8,
                    metadata={'type': 'skills', 'persistent': True}
                )
            
            logger.info(f"Initialized session memory for {session_id}")
            
        except Exception as e:
            logger.error(f"Error initializing session memory: {e}")
    
    @staticmethod
    def _process_message_for_entities(session, message, is_dm=False):
        """
        Process message text to extract entities
        
        Args:
            session (GameSession): Game session
            message (str): Message text
            is_dm (bool): Whether this is a DM message
            
        Returns:
            None
        """
        try:
            # Simple entity extraction with NER would be better
            # This is a simplified version that looks for capitalized words
            
            # Entities are often proper nouns (capitalized)
            words = message.split()
            for i, word in enumerate(words):
                # Skip small words and those that start sentences
                if len(word) < 3 or (i == 0):
                    continue
                
                # Check for capitalized words
                if word[0].isupper() and word[1:].islower():
                    # Clean up punctuation
                    clean_word = word.strip(',.!?:;\'\"()')
                    
                    # Skip common capitalized words that aren't entities
                    common_words = ['The', 'And', 'But', 'Or', 'For', 'With', 'You', 'Your']
                    if clean_word in common_words:
                        continue
                    
                    # Get surrounding context
                    start_idx = max(0, i - 5)
                    end_idx = min(len(words), i + 5)
                    context = ' '.join(words[start_idx:end_idx])
                    
                    # Try to determine entity type
                    entity_type = "unknown"
                    
                    # Check for location indicators
                    location_indicators = ['town', 'city', 'village', 'castle', 'fortress', 'inn', 'tavern', 
                                          'dungeon', 'cave', 'forest', 'mountain', 'river', 'lake', 'temple']
                    
                    # Check for NPC indicators
                    npc_indicators = ['says', 'said', 'man', 'woman', 'elf', 'dwarf', 'halfling', 'gnome', 
                                     'merchant', 'guard', 'knight', 'wizard', 'sorcerer', 'priest']
                    
                    # Check for item indicators
                    item_indicators = ['sword', 'dagger', 'bow', 'staff', 'wand', 'scroll', 'potion',
                                      'armor', 'shield', 'amulet', 'ring', 'cloak', 'boots']
                    
                    # Context-based type determination
                    context_lower = context.lower()
                    if any(indicator in context_lower for indicator in location_indicators):
                        entity_type = "location"
                    elif any(indicator in context_lower for indicator in npc_indicators):
                        entity_type = "npc"
                    elif any(indicator in context_lower for indicator in item_indicators):
                        entity_type = "item"
                    
                    # Add or update the entity
                    if clean_word in session.important_entities:
                        # Update existing entity
                        entity = session.important_entities[clean_word]
                        # Only update description if it's from the DM 
                        # (DM descriptions are more authoritative than player ones)
                        if is_dm:
                            entity['description'] = context
                        # Increment importance for repeated mentions
                        entity['importance'] = min(10, entity.get('importance', 5) + 1)
                        entity['updated_at'] = datetime.utcnow().isoformat()
                    else:
                        # Add new entity
                        session.add_important_entity(
                            clean_word,
                            entity_type,
                            context,
                            importance=6 if is_dm else 5  # DM entities are slightly more important
                        )
            
            # Check for player decisions (if not a DM message)
            if not is_dm:
                decision_indicators = ['decide', 'decision', 'choose', 'choice', 'opt', 'option', 'elect', 'selection']
                message_lower = message.lower()
                
                if any(indicator in message_lower for indicator in decision_indicators):
                    # Record as a player decision
                    session.record_player_decision(message)
        except Exception as e:
            logger.error(f"Error processing message for entities: {e}")
    
    @staticmethod
    def _update_session_summary_if_needed(session):
        """
        Update session summary if needed
        
        Args:
            session (GameSession): Game session
            
        Returns:
            None
        """
        try:
            # Check if we have at least 10 messages
            if len(session.history) >= 10:
                # Check if we have no summary yet
                if not session.session_summary or session.session_summary == "Session beginning. No summary yet.":
                    GameService._generate_session_summary(session)
                # Or check if we have at least 10 new messages since the last summary generation
                elif len(session.history) % 10 == 0:
                    GameService._generate_session_summary(session)
        except Exception as e:
            logger.error(f"Error updating session summary: {e}")
    
    @staticmethod
    def _generate_session_summary(session):
        """
        Generate a summary of the gaming session using the summarization service.
        
        Args:
            session (GameSession): Game session object
            
        Returns:
            str: A concise summary of the gaming session
        """
        try:
            # Import the summarization service here to avoid circular imports
            from app.services.summarization_service import SummarizationService
            
            # Initialize the summarization service
            summarization_service = SummarizationService()
            
            # Use recent messages from the session history
            # Typically we'd use the last 20 messages or so
            recent_messages = session.history[-20:] if len(session.history) >= 20 else session.history
            
            # Extract the text content from messages
            message_texts = []
            for msg in recent_messages:
                if isinstance(msg, dict):
                    sender = msg.get('sender', 'Unknown')
                    content = msg.get('message', '')
                    if sender and content:
                        message_texts.append(f"{sender}: {content}")
                else:
                    message_texts.append(str(msg))
            
            # Join messages into a single text
            full_text = " ".join(message_texts)
            
            # Call the summarization service
            summary = summarization_service.summarize_text(
                text=full_text,
                max_length=150,
                min_length=30  # Adjust based on your requirements
            )
            
            # Update the session summary
            session.session_summary = summary
            
            # Store summary as a memory for retrieval
            try:
                from app.services.memory_service_enhanced import EnhancedMemoryService
                memory_service = EnhancedMemoryService()
                
                # Store as a special summary memory
                memory_service.store_memory_with_text(
                    content=summary,
                    memory_type='summary',
                    session_id=session.session_id,
                    character_id=session.character_id,
                    user_id=session.user_id,
                    importance=10,  # Maximum importance
                    metadata={
                        'type': 'session_summary',
                        'history_range': f"0-{len(session.history)}"
                    }
                )
            except Exception as memory_e:
                logger.error(f"Error storing summary memory: {memory_e}")
            
            return summary
            
        except Exception as e:
            # Log the error but provide a fallback summary
            logger.error(f"Failed to generate summary for session {session.session_id}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            session.session_summary = f"Gaming session with {len(session.history)} interactions"
            return session.session_summary
            
    @staticmethod
    def _calculate_message_importance(message):
        """
        Calculate importance score for a message
        
        Args:
            message (str): Message text
            
        Returns:
            int: Importance score (1-10)
        """
        # Base importance
        importance = 5
        
        # Adjust based on text length
        if len(message) > 500:
            importance += 1
        
        # Key terms indicating important information
        important_terms = [
            "quest", "mission", "objective", "task", "goal",
            "important", "critical", "crucial", "essential", "vital",
            "remember", "forget", "keep in mind", "note",
            "secret", "hidden", "discover", "reveal", "find",
            "key", "password", "code", "combination",
            "treasure", "artifact", "item", "weapon", "armor",
            "danger", "threat", "enemy", "villain", "boss",
            "ally", "friend", "companion", "helper",
            "location", "place", "map", "direction", "path"
        ]
        
        # Check for important terms
        for term in important_terms:
            if term.lower() in message.lower():
                importance += 1
                # Avoid double-counting similar terms
                break
        
        # Check for proper nouns (simplified approach)
        words = message.split()
        for word in words:
            if len(word) > 1 and word[0].isupper() and word[1:].islower():
                importance += 1
                break
        
        # Cap importance
        return min(10, importance)
    
    @staticmethod
    def _get_latest_entities(session, limit=3):
        """
        Get the most recently updated entities
        
        Args:
            session (GameSession): Game session
            limit (int): Maximum number of entities to return
            
        Returns:
            list: List of entities
        """
        try:
            entities = []
            for name, data in session.important_entities.items():
                entities.append({
                    'name': name,
                    'type': data.get('type', 'unknown'),
                    'description': data.get('description', ''),
                    'importance': data.get('importance', 5),
                    'updated_at': data.get('updated_at')
                })
            
            # Sort by updated_at (most recent first)
            entities.sort(key=lambda e: e.get('updated_at', ''), reverse=True)
            
            # Return limited number
            return entities[:limit]
            
        except Exception as e:
            logger.error(f"Error getting latest entities: {e}")
            return []
    
    @staticmethod
    def roll_dice(dice_type, modifier=0, user_id=None, session_id=None):
        """
        Roll a die of the specified type with an optional modifier
        
        Args:
            dice_type (str): The type of die to roll (e.g., 'd20', 'd6')
            modifier (int): Modifier to add to the roll
            user_id (str): The ID of the user rolling the die
            session_id (str): The current game session ID
            
        Returns:
            dict: Result with success status and roll information
        """
        try:
            # Parse the dice type (e.g., "d20" -> 20)
            if not dice_type.startswith('d'):
                return {'success': False, 'error': 'Invalid dice type format'}
                
            try:
                sides = int(dice_type[1:])
            except ValueError:
                return {'success': False, 'error': 'Invalid dice type'}
            
            if sides <= 0:
                return {'success': False, 'error': 'Dice must have at least 1 side'}
            
            # Convert modifier to integer if it's not already
            if not isinstance(modifier, int):
                try:
                    modifier = int(modifier)
                except (ValueError, TypeError):
                    modifier = 0
            
            # Roll the die (generate a random number)
            import random
            result = random.randint(1, sides)
            
            # Apply modifier
            modified_result = result + modifier
            
            # Generate a roll ID for tracking
            roll_id = str(uuid.uuid4())
            
            # Store the roll result in the database if session is active
            if session_id is not None and user_id is not None:
                db = get_db()
                if db is not None:
                    # Record the roll in a dedicated collection
                    db.dice_rolls.insert_one({
                        'roll_id': roll_id,
                        'session_id': session_id,
                        'user_id': user_id,
                        'dice_type': dice_type,
                        'raw_result': result,
                        'modifier': modifier,
                        'final_result': modified_result,
                        'timestamp': datetime.utcnow()
                    })
                    
                    # Add roll to the session history as a special message
                    GameService._add_roll_to_session(
                        session_id=session_id,
                        roll_id=roll_id,
                        dice_type=dice_type,
                        result=result,
                        modifier=modifier,
                        modified_result=modified_result
                    )
            
            # Return success with roll information
            return {
                'success': True,
                'roll_id': roll_id,
                'dice': dice_type,
                'result': result,
                'modifier': modifier,
                'modified_result': modified_result
            }
        
        except Exception as e:
            logger.error(f"Error rolling dice: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {'success': False, 'error': str(e)}

    @staticmethod
    def _add_roll_to_session(session_id, roll_id, dice_type, result, modifier, modified_result):
        """Add a dice roll to the session history"""
        try:
            db = get_db()
            if db is None:
                return False
                
            # Get the session
            session_data = db.sessions.find_one({'session_id': session_id})
            if session_data is None:
                return False
                
            # Format roll message
            modifier_text = f" + {modifier}" if modifier > 0 else f" - {abs(modifier)}" if modifier < 0 else ""
            roll_message = f"🎲 Rolled {dice_type}: {result}{modifier_text} = {modified_result}"
            
            # Create message entry with special roll type
            message_entry = {
                'sender': 'system',
                'message': roll_message,
                'timestamp': datetime.utcnow().isoformat(),
                'type': 'dice_roll',
                'roll_data': {
                    'roll_id': roll_id,
                    'dice_type': dice_type,
                    'result': result,
                    'modifier': modifier,
                    'modified_result': modified_result
                }
            }
            
            # Add to history
            history = session_data.get('history', [])
            history.append(message_entry)
            
            # Update session
            db.sessions.update_one(
                {'session_id': session_id},
                {'$set': {'history': history, 'updated_at': datetime.utcnow()}}
            )
            
            return True
        except Exception as e:
            logger.error(f"Error adding roll to session: {e}")
            return False