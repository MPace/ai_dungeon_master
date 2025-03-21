"""
Characters routes
"""
from flask import render_template, request, redirect, url_for, flash, jsonify, session
from app.characters import characters_bp
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

@characters_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard showing characters and drafts"""
    user_id = session.get('user_id')
    logger.info(f"Dashboard accessed by user ID: {user_id}")
    
    # Get characters
    characters_result = CharacterService.list_characters(user_id)
    if not characters_result['success']:
        flash('Error loading characters: ' + characters_result.get('error', 'Unknown error'), 'error')
        characters = []
    else:
        characters = characters_result['characters']
    
    # Get drafts
    drafts_result = CharacterService.list_character_drafts(user_id)
    if not drafts_result['success']:
        flash('Error loading drafts: ' + drafts_result.get('error', 'Unknown error'), 'error')
        drafts = []
    else:
        drafts = drafts_result['drafts']
    
    logger.info(f"Rendering dashboard with {len(characters)} characters and {len(drafts)} drafts")
    
    return render_template('user.html',
                          username=session.get('username', 'User'),
                          characters=characters,
                          drafts=drafts)

@characters_bp.route('/create')
@login_required
def create():
    """Character creation page"""
    # Check if we're loading a draft
    draft_id = request.args.get('draft_id')
    draft = None
    
    if draft_id:
        draft_result = CharacterService.get_character(draft_id, session['user_id'])
        if draft_result['success']:
            draft = draft_result['character']
    
    return render_template('create.html', draft=draft)

@characters_bp.route('/api/save-character', methods=['POST'])
@login_required
def save_character():
    """API endpoint to save a character"""
    try:
        # Get character data from request
        character_data = request.json
        
        if not character_data:
            return jsonify({
                'success': False,
                'error': 'No character data provided'
            }), 400
        
        # Get user_id from session
        user_id = session.get('user_id')
        
        # Check for submission ID to prevent duplicate saves
        submission_id = character_data.get('submissionId')
        
        # Save the character
        result = CharacterService.create_character(character_data, user_id)
        
        if result['success']:
            character = result['character']
            
            # If successful, return the character ID
            return jsonify({
                'success': True,
                'character_id': character.character_id,
                'message': 'Character saved successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to save character')
            }), 500
    
    except Exception as e:
        logger.error(f"Error in save_character route: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@characters_bp.route('/api/save-character-draft', methods=['POST'])
@login_required
def save_character_draft():
    """API endpoint to save a character draft"""
    try:
        # Get character data from request
        character_data = request.json
        
        if not character_data:
            return jsonify({
                'success': False,
                'error': 'No character data provided'
            }), 400
        
        # Get user_id from session
        user_id = session.get('user_id')
        
        # Save the character draft
        result = CharacterService.save_character_draft(character_data, user_id)
        
        if result['success']:
            character = result['character']
            
            # If successful, return the character ID
            return jsonify({
                'success': True,
                'character_id': character.character_id,
                'message': 'Character draft saved successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to save character draft')
            }), 500
    
    except Exception as e:
        logger.error(f"Error in save_character_draft route: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@characters_bp.route('/api/character/<character_id>', methods=['GET'])
@login_required
def get_character(character_id):
    """API endpoint to retrieve a character"""
    user_id = session.get('user_id')
    
    result = CharacterService.get_character(character_id, user_id)
    
    if result['success']:
        character = result['character']
        return jsonify({
            'success': True,
            'character': character.to_dict()
        })
    else:
        return jsonify({
            'success': False,
            'error': result.get('error', 'Character not found')
        }), 404

@characters_bp.route('/api/delete-character/<character_id>', methods=['POST'])
@login_required
def delete_character(character_id):
    """API endpoint to delete a character"""
    user_id = session.get('user_id')
    
    result = CharacterService.delete_character(character_id, user_id)
    
    return jsonify(result)

@characters_bp.route('/api/delete-draft/<draft_id>', methods=['POST'])
@login_required
def delete_draft(draft_id):
    """API endpoint to delete a character draft"""
    user_id = session.get('user_id')
    
    result = CharacterService.delete_character_draft(draft_id, user_id)
    
    return jsonify(result)