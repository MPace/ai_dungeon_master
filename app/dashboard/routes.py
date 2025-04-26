"""
Dashboard routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask import current_app, abort
from app.services.character_service import CharacterService
from app.extensions import login_required
import logging
from datetime import datetime
import traceback
import os
import json

logger = logging.getLogger(__name__)

# Create Blueprint
dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    """
    Render dashboard page with React content
    """
    try:
        user_id = session.get('user_id')
        username = session.get('username', 'User')
        
        logger.info(f"Dashboard accessed by user: {username} (ID: {user_id})")
        
        # Load Vite manifest
        manifest = load_vite_manifest()
        if manifest is None:
            abort(500, description="Vite Manifest file is missing or invalid. Cannot load application assets.") 

        entry_point_key = 'src/index.jsx'
        if entry_point_key not in manifest:
            current_app.logger.error(f"Entry point '{entry_point_key}' not found in Vite manifest.")
            abort(500, description=f"Entry point '{entry_point_key}' not found in Vite manifest.")

        manifest_entry = manifest[entry_point_key]
        js_file = manifest_entry.get('file')
        css_files = manifest_entry.get('css', [])
        css_file = css_files[0] if css_files else None

        if not js_file:
            current_app.logger.error(f"JS file path not found for entry point '{entry_point_key}' in manifest.")
            abort(500, description=f"JS file path missing in manifest for entry point '{entry_point_key}'.")

        # Use the same base URL as used in character creation
        VITE_BASE_URL = "https://staging.arcanedm.com:8443/static/build/"
        
        return render_template('dashboard.html',
                              username=username,
                              react_js_file=f"{VITE_BASE_URL}{js_file}" if js_file else None,
                              react_css_file=f"{VITE_BASE_URL}{css_file}" if css_file else None)
    except Exception as e:
        logger.error(f"Error rendering dashboard: {str(e)}")
        logger.error(traceback.format_exc())
        flash('Error loading dashboard', 'error')
        return redirect(url_for('auth.index'))
        
# Add the same helper function used in characters/routes.py
def load_vite_manifest():
    manifest_path = os.path.join(current_app.static_folder, 'build', '.vite', 'manifest.json')
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
            current_app.logger.debug("Vite manifest loaded successfully")
            return manifest
    except FileNotFoundError:
        current_app.logger.error(f"Vite manifest not found at {manifest_path}")
        current_app.logger.error("Did you forget to run 'npm run build' in the frontend directory?")
    except json.JSONDecodeError:
        current_app.logger.error(f"Error decoding Vite manifest file: {manifest_path}")
    except Exception as e:
         current_app.logger.error(f"An unexpected error occurred loading manifest: {e}")
    return None # Return None if manifest cannot be loaded/parsed

@dashboard_bp.route('/api/characters')
@login_required
def api_get_characters():
    """
    API endpoint to get all characters for a user
    """
    try:
        user_id = session.get('user_id')
        
        logger.info(f"API - Getting characters for user ID: {user_id}")
        
        # Use CharacterService to get characters
        result = CharacterService.list_characters(user_id)
        
        if result.get('success', False):
            characters = result.get('characters', [])
            
            # Process characters to ensure proper data format for frontend
            processed_characters = []
            for character in characters:
                if hasattr(character, 'to_dict'):
                    char_dict = character.to_dict()
                    
                    # Ensure last_played is formatted correctly
                    if char_dict.get('last_played'):
                        try:
                            # Convert to string if it's a datetime object
                            if hasattr(char_dict['last_played'], 'isoformat'):
                                char_dict['last_played'] = char_dict['last_played'].isoformat()
                        except Exception as e:
                            logger.warning(f"Error formatting last_played date: {e}")
                    
                    processed_characters.append(char_dict)
                else:
                    processed_characters.append(character)
            
            logger.info(f"Returning {len(processed_characters)} characters")
            return jsonify({'success': True, 'characters': processed_characters})
        else:
            error_msg = result.get('error', 'Unknown error fetching characters')
            logger.error(f"API Error: {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 500
    
    except Exception as e:
        logger.error(f"Exception in api_get_characters: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@dashboard_bp.route('/api/character-drafts')
@login_required
def api_get_drafts():
    """
    API endpoint to get all character drafts for a user
    """
    try:
        user_id = session.get('user_id')
        
        logger.info(f"API - Getting character drafts for user ID: {user_id}")
        
        # Use CharacterService to get drafts
        result = CharacterService.list_character_drafts(user_id)
        
        if result.get('success', False):
            drafts = result.get('drafts', [])
            
            # Process drafts to ensure proper data format for frontend
            processed_drafts = []
            for draft in drafts:
                if hasattr(draft, 'to_dict'):
                    draft_dict = draft.to_dict()
                    
                    # Ensure lastUpdated is included and formatted correctly
                    if 'updated_at' in draft_dict and not 'lastUpdated' in draft_dict:
                        draft_dict['lastUpdated'] = draft_dict['updated_at']
                    
                    # Ensure lastStep is included
                    if 'lastStepCompleted' in draft_dict and not 'lastStep' in draft_dict:
                        draft_dict['lastStep'] = draft_dict['lastStepCompleted']
                    
                    processed_drafts.append(draft_dict)
                else:
                    processed_drafts.append(draft)
            
            logger.info(f"Returning {len(processed_drafts)} drafts")
            return jsonify({'success': True, 'drafts': processed_drafts})
        else:
            error_msg = result.get('error', 'Unknown error fetching drafts')
            logger.error(f"API Error: {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 500
    
    except Exception as e:
        logger.error(f"Exception in api_get_drafts: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@dashboard_bp.route('/api/character/<character_id>')
@login_required
def api_get_character(character_id):
    """
    API endpoint to get a specific character
    """
    try:
        user_id = session.get('user_id')
        
        logger.info(f"API - Getting character {character_id} for user ID: {user_id}")
        
        # Use CharacterService to get character
        result = CharacterService.get_character(character_id, user_id)
        
        if result.get('success', False):
            character = result.get('character')
            
            if character:
                # Convert to dict if it's a Character object
                if hasattr(character, 'to_dict'):
                    character_dict = character.to_dict()
                else:
                    character_dict = character
                
                logger.info(f"Returning character: {character_dict.get('name', 'Unknown')}")
                return jsonify({'success': True, 'character': character_dict})
            else:
                logger.warning(f"Character not found: {character_id}")
                return jsonify({'success': False, 'error': 'Character not found'}), 404
        else:
            error_msg = result.get('error', 'Unknown error fetching character')
            logger.error(f"API Error: {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 500
    
    except Exception as e:
        logger.error(f"Exception in api_get_character: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@dashboard_bp.route('/api/character-draft/<draft_id>')
@login_required
def api_get_draft(draft_id):
    """
    API endpoint to get a specific character draft
    """
    try:
        user_id = session.get('user_id')
        
        logger.info(f"API - Getting character draft {draft_id} for user ID: {user_id}")
        
        # Use CharacterService to get draft
        result = CharacterService.get_character_draft(draft_id, user_id)
        
        if result.get('success', False):
            draft = result.get('character')
            
            if draft:
                # Convert to dict if it's a Character object
                if hasattr(draft, 'to_dict'):
                    draft_dict = draft.to_dict()
                else:
                    draft_dict = draft
                
                logger.info(f"Returning draft: {draft_dict.get('name', 'Unnamed')}")
                return jsonify({'success': True, 'draft': draft_dict})
            else:
                logger.warning(f"Draft not found: {draft_id}")
                return jsonify({'success': False, 'error': 'Draft not found'}), 404
        else:
            error_msg = result.get('error', 'Unknown error fetching draft')
            logger.error(f"API Error: {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 500
    
    except Exception as e:
        logger.error(f"Exception in api_get_draft: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500