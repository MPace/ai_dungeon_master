"""
Memory Management API Routes
"""
from flask import request, jsonify, session
from app.game import game_bp
from app.services.game_service import GameService
from app.extensions import login_required, get_db
from app.services.memory_service_enhanced import EnhancedMemoryService
import logging

logger = logging.getLogger(__name__)

@game_bp.route('/api/memories/<session_id>', methods=['GET'])
@login_required
def get_session_memories(session_id):
    """Get memories for a session"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        # Get query parameters
        limit = request.args.get('limit', default=20, type=int)
        memory_type = request.args.get('type', default='all')
        
        # Get memories
        result = GameService.get_session_memories(
            session_id=session_id,
            user_id=user_id,
            limit=limit,
            memory_type=memory_type
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error retrieving session memories: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@game_bp.route('/api/memories/<session_id>/pin', methods=['POST'])
@login_required
def pin_memory(session_id):
    """Pin a memory to a session"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        # Get request data
        data = request.json
        memory_id = data.get('memory_id')
        importance = data.get('importance')
        note = data.get('note')
        
        if not memory_id:
            return jsonify({'success': False, 'error': 'Memory ID is required'}), 400
        
        # Pin memory
        result = GameService.pin_memory(
            session_id=session_id,
            memory_id=memory_id,
            user_id=user_id,
            importance=importance,
            note=note
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error pinning memory: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@game_bp.route('/api/memories/<session_id>/unpin', methods=['POST'])
@login_required
def unpin_memory(session_id):
    """Unpin a memory from a session"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        # Get request data
        data = request.json
        memory_id = data.get('memory_id')
        
        if not memory_id:
            return jsonify({'success': False, 'error': 'Memory ID is required'}), 400
        
        # Unpin memory
        result = GameService.unpin_memory(
            session_id=session_id,
            memory_id=memory_id,
            user_id=user_id
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error unpinning memory: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@game_bp.route('/api/entities/<session_id>', methods=['GET'])
@login_required
def get_entities(session_id):
    """Get important entities for a session"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        # Get entities
        result = GameService.get_important_entities(
            session_id=session_id,
            user_id=user_id
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error retrieving entities: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@game_bp.route('/api/entities/<session_id>/update', methods=['POST'])
@login_required
def update_entity(session_id):
    """Update an entity in a session"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        # Get request data
        data = request.json
        entity_name = data.get('name')
        entity_data = data.get('data')
        
        if not entity_name or not entity_data:
            return jsonify({'success': False, 'error': 'Entity name and data are required'}), 400
        
        # Update entity
        result = GameService.update_entity(
            session_id=session_id,
            entity_name=entity_name,
            entity_data=entity_data,
            user_id=user_id
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error updating entity: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@game_bp.route('/api/summary/<session_id>', methods=['GET'])
@login_required
def get_summary(session_id):
    """Get summary for a session"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        # Get summary
        result = GameService.get_session_summary(
            session_id=session_id,
            user_id=user_id
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error retrieving summary: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    
@game_bp.route('/api/memories/<session_id>', methods=['POST'])
@login_required
def create_memory(session_id):
    """Create a new memory for a session"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        # First check if the user has access to this session
        db = get_db()
        if db is None:
            return jsonify({'success': False, 'error': 'Database connection error'}), 500
            
        # Verify session ownership
        game_session = db.sessions.find_one({
            'session_id': session_id,
            'user_id': user_id
        })
        
        if not game_session:
            return jsonify({'success': False, 'error': 'Session not found or access denied'}), 403
        
        # Get request data
        data = request.json
        content = data.get('content')
        memory_type = data.get('memory_type', 'short_term')
        importance = data.get('importance', 5)
        metadata = data.get('metadata', {})
        
        if not content:
            return jsonify({'success': False, 'error': 'Memory content is required'}), 400
        
        # Initialize memory service
        memory_service = EnhancedMemoryService()
        
        # Store memory
        result = memory_service.store_memory_with_text(
            content=content,
            memory_type=memory_type,
            session_id=session_id,
            character_id=game_session.get('character_id'),
            user_id=user_id,
            importance=importance,
            metadata=metadata
        )
        
        if result.get('success', False):
            # Get memory ID from result
            memory = result.get('memory')
            memory_id = memory.memory_id if memory else None
            
            # Check if this should be pinned
            if metadata.get('pinned', False):
                from app.services.game_service import GameService
                
                # Pin the memory
                pin_result = GameService.pin_memory(
                    session_id=session_id,
                    memory_id=memory_id,
                    user_id=user_id,
                    importance=importance,
                    note=metadata.get('note')
                )
                
                if not pin_result.get('success', False):
                    logger.warning(f"Failed to pin memory: {pin_result.get('error')}")
            
            return jsonify({
                'success': True,
                'memory_id': memory_id,
                'message': 'Memory created successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to create memory')
            }), 500
            
    except Exception as e:
        logger.error(f"Error creating memory: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500