"""
Game routes
"""
from flask import render_template, request, redirect, url_for, flash, jsonify, session
from app.game import game_bp
from app.services.game_service import GameService
from app.services.character_service import CharacterService
from app.services.auth_service import AuthService
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logger.info(f"Checking authentication for route: {request.path}")
        
        if 'user_id' not in session:
            logger.error(f"AUTHENTICATION FAILED: No user_id in session for {request.path}")
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('auth.index'))
            
        # Authentication successful
        logger.info(f"Authentication successful for user: {session.get('username', 'Unknown')}")
        return f(*args, **kwargs)
    return decorated_function

@game_bp.route('/play/<character_id>')
@login_required
def play(character_id):
    """Game interface page for playing with a specific character"""
    user_id = session.get('user_id')
    
    try:
        # Get character data
        character_result = CharacterService.get_character(character_id, user_id)
        
        if not character_result['success']:
            flash('Character not found', 'error')
            return redirect(url_for('characters.dashboard'))
        
        character = character_result['character']
        
        # Render game interface
        return render_template('dm.html', character=character.to_dict())
    
    except Exception as e:
        logger.error(f"Error in play_game route: {e}")
        import traceback
        logger.error(traceback.format_exc())
        flash('Error loading character: ' + str(e), 'error')
        return redirect(url_for('characters.dashboard'))

@game_bp.route('/api/send-message', methods=['POST'])
@login_required
def send_message():
    """Process a message from the player and return a DM response"""
    data = request.json
    message = data.get('message', '')
    session_id = data.get('session_id')
    character_data = data.get('character_data')
    
    user_id = session.get('user_id')
    
    # Send message and get response
    result = GameService.send_message(session_id, message, user_id)
    
    if result['success']:
        return jsonify({
            'response': result['response'],
            'session_id': result['session_id'],
            'game_state': result['game_state']
        })
    else:
        return jsonify({
            'error': result.get('error', 'Failed to process message')
        }), 500

@game_bp.route('/api/roll-dice', methods=['POST'])
@login_required
def roll_dice():
    """Handle dice rolling requests"""
    data = request.json
    dice_type = data.get('dice', 'd20')
    modifier = data.get('modifier', 0)
    
    # Roll the dice
    result = GameService.roll_dice(dice_type, modifier)
    
    if result['success']:
        return jsonify({
            'dice': result['dice'],
            'result': result['result'],
            'modifier': result['modifier'],
            'modified_result': result['modified_result']
        })
    else:
        return jsonify({
            'error': result.get('error', 'Failed to roll dice')
        }), 400