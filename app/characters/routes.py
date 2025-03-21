"""
Characters routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from app.characters import characters_bp
from app.services.character_service import CharacterService
from app.services.auth_service import AuthService
from functools import wraps
from datetime import datetime
from app.extensions import login_required
import logging
import uuid

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
def save_character_route():
    try:
        # Get character data from request
        character_data = request.json
        
        if character_data is None:
            return jsonify({
                'success': False,
                'error': 'No character data provided'
            }), 400
        
        # Get user_id from session
        user_id = session.get('user_id')
        
        if user_id is None:
            return jsonify({
                'success': False,
                'error': 'User not logged in'
            }), 401
        
        # Check for submission ID to prevent duplicate saves
        submission_id = character_data.get('submissionId')
        
        if submission_id is not None:
            # Check if we've seen this submission before
            recent_submission = CharacterService.check_submission(submission_id, user_id)
            
            if recent_submission is not None:
                # This is a duplicate submission
                return jsonify({
                    'success': True,
                    'character_id': recent_submission.get('character_id'),
                    'message': 'Character already saved (duplicate submission)',
                    'isDuplicate': True
                })
        
        # Add user_id to character data
        character_data['user_id'] = user_id
        
        # Mark as complete (not a draft)
        character_data['isDraft'] = False
        character_data['completedAt'] = datetime.utcnow().isoformat()
        
        # Get the character_id
        character_id = character_data.get('character_id')
        
        if character_id is None:
            # Generate a new ID if none exists
            character_id = str(uuid.uuid4())
            character_data['character_id'] = character_id
        
        # Check if character already exists
        existing_character = CharacterService.get_character(character_id, user_id)
        
        if existing_character is not None and existing_character.get('isDraft') is not True:
            # This character already exists as a completed character
            # Log this submission to prevent future duplicates
            if submission_id is not None:
                CharacterService.log_submission(submission_id, character_id, user_id)
            
            # Return success but don't save again
            return jsonify({
                'success': True,
                'character_id': character_id,
                'message': 'Character already exists',
                'alreadyExists': True
            })
        
        # Delete any existing drafts with this ID
        CharacterService.delete_character_draft(character_id, user_id)
        
        # Now save the character
        result = CharacterService.create_character(character_data, user_id)
        saved_id = character_id if result ['succes'] else None

        if saved_id is not None:
            # Log this submission to prevent future duplicates
            if submission_id is not None:
                CharacterService.log_submission(submission_id, saved_id, user_id)
            
            return jsonify({
                'success': True,
                'character_id': saved_id,
                'message': 'Character saved successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to save character'
            }), 500
    
    except Exception as e:
        import traceback
        traceback.print_exc()
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

@characters_bp.route('/api/characters', methods=['GET'])
def list_characters_route():
    # Get user_id from session
    user_id = session.get('user_id')
    
    if user_id is None:
        return jsonify({
            'success': False,
            'error': 'User not logged in'
        }), 401
    
    characters = CharacterService.list_characters(user_id)
    
    return jsonify({
        'success': True,
        'characters': characters
    })

@characters_bp.route('/api/character/<character_id>', methods=['GET'])
def get_character_route(character_id):
    # Get user_id from session
    user_id = session.get('user_id')
    
    if user_id is None:
        return jsonify({
            'success': False,
            'error': 'User not logged in'
        }), 401
    
    character = CharacterService.get_character(character_id, user_id)
    
    if character:
        return jsonify({
            'success': True,
            'character': character
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Character not found'
        })

@characters_bp.route('/api/delete-character/<character_id>', methods=['POST'])
@login_required
def delete_character_route(character_id):
    try:
        # Get user_id from session
        user_id = session.get('user_id')
        logger.info(f"Deleting character {character_id} for user {user_id}")
        
        # Use service to delete character
        result = CharacterService.delete_character(character_id, user_id)
        
        return jsonify(result)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@characters_bp.route('/api/delete-draft/<draft_id>', methods=['POST'])
@login_required
def delete_draft_route(draft_id):
    try:
        # Get user_id from session
        user_id = session.get('user_id')
        logger.info(f"Deleting draft {draft_id} for user {user_id}")
        
        # Use service to delete draft
        result = CharacterService.delete_character_draft(draft_id, user_id)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error in delete_draft_route: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500