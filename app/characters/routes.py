"""
Characters routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, current_app, abort
from app.characters import characters_bp
from app.services.character_service import CharacterService
from app.services.auth_service import AuthService
from functools import wraps
from datetime import datetime
from app.extensions import login_required
import logging
import uuid
import os
import yaml
import json

logger = logging.getLogger(__name__)


DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))
WORLDS_DIR = os.path.join(DATA_DIR, 'worlds')
CAMPAIGNS_DIR = os.path.join(DATA_DIR, 'campaigns')
CLASSES_DIR = os.path.join(DATA_DIR, 'classes')
RACES_DIR = os.path.join(DATA_DIR, 'races')
BACKGROUNDS_DIR = os.path.join(DATA_DIR, 'backgrounds')
VITE_BASE_URL = "https://staging.arcanedm.com:8443/static/build/" # Base URL for Vite assets



# Helper function to load manifest 
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
    """Character creation page - loads React app and handles drafts"""
    # Check if we're loading a draft
    current_app.logger.info("Accessing character creation route")

    # Load Draft Data
    draft_id = request.args.get('draft_id')
    draft_data = None
    
    if draft_id:
        current_app.logger.info(f"Attempting to load draft with ID: {draft_id}")
        draft_result = CharacterService.get_character_draft(draft_id, session['user_id'])
        if draft_result and draft_result.get('success'):
            draft_obj = draft_result.get('character')
            if draft_obj:
                draft_data = draft_obj.to_dict() if hasattr(draft_obj, 'to_dict') else draft_obj
                current_app.logger.info(f"Draft loaded: {draft_data.get('name', 'Unnamed')}")
            else:
                current_app.logger.warning(f"Draft service returned success but no character object for ID: {draft_id}")
                flash(f"Could not load draft '{draft_id}'. Starting fresh.", 'warning')
        else:
            current_app.logger.warning(f"Failed to load draft ID: {draft_id}. Error: {draft_result.get('error')}")
            flash(f"Could not load draft '{draft_id}'. Starting fresh.", 'warning')

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

    return render_template(
        'create.html',
        draft_character_data=json.dumps(draft_data) if draft_data else None,
        react_js_file=f"https://staging.arcanedm.com:8443/static/build/{js_file}" if js_file else None,
        react_css_file=f"https://staging.arcanedm.com:8443/static/build/{css_file}" if css_file else None,
        username=session.get('username', 'User')
    )

@characters_bp.route('/api/save-character', methods=['POST'])
@login_required
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
        existing_result = CharacterService.get_character(character_id, user_id)
        existing_character = existing_result.get('character') if existing_result.get('success', False) else None
        
        if existing_character is not None and not existing_character.is_draft:
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
        
        if result['success']:
            # Get the character_id from the result
            saved_id = result['character'].character_id if hasattr(result['character'], 'character_id') else character_id
            
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
                'error': result.get('error', 'Failed to save character')
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
    
@characters_bp.route('/api/worlds', methods=['GET'])
@login_required
def get_worlds():
    """API endpoint to get a list of available worlds"""
    worlds = []
    worlds_dir = os.path.join(current_app.root_path, '..', 'data', 'worlds')
    
    try:
        if not os.path.exists(worlds_dir):
            current_app.logger.error(f"Worlds directory not found: {worlds_dir}")
            return jsonify({"success": False, "error": "Worlds data not found"}), 500
    
        for filename in os.listdir(worlds_dir):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                file_path = os.path.join(worlds_dir, filename)
                current_app.logger.debug(f"Processiong world file: {filename}")
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        world_data = yaml.safe_load(f)
                        if not world_data:
                            current_app.logger.warning(f"World file {filename} is empty or invalid")
                            continue
                        
                        # Extract required and optional info
                        world_id = world_data.get('id', filename.split('.')[0]) # Use file name as ID if not specified
                        world_name = world_data.get("name")

                        # Skip if essential data is missing
                        if not world_name:
                            current_app.logger.warning(f"World file {filename} is missing 'name'. Skipping")
                            continue

                        image_path = world_data.get("image")
                        if image_path and image_path.startswith('/') and not image_path.startswith('http'):
                            full_image_url = f"{VITE_BASE_URL}{image_path}"
                            world_data["image"] = full_image_url
                            current_app.logger.debug(f"Contstructed full image URL: {full_image_url}")
                        
                        elif image_path:
                            world_data["image"] = image_path.strip('\'"')
                        
                        # Extract only necessary info for the list
                        worlds.append({
                            "id": world_id,
                            "name": world_name,
                            "description": world_data.get("description", "No description available"),
                            "image": world_data.get("image", None)
                        })
                        current_app.logger.debug(f"Successfully loaded world: {world_name} (ID: {world_id})")
                except yaml.YAMLError as e:
                    current_app.logger.error(f"Error parsing YAML file {filename}: {e}")        
                except Exception as e:
                    current_app.logger.error(f"Error loading world file {filename}: {e}")
        
        current_app.logger.info(f"Found {len(worlds)} worlds.")
        return jsonify({"success": True, "worlds": worlds})
    
    except Exception as e:
        current_app.logger.error(f"Error reading worlds directory {WORLDS_DIR}: {e}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": "Failed to retrieve worlds."}), 500
        

@characters_bp.route('/api/campaigns/<world_id>', methods=['GET'])
@login_required
def get_campaigns(world_id):
    """API endpoint to get pre-made campaigns for a specific world."""
    campaigns = []
    default_campaign = {
        "id": "dm_created",
        "name": "Custom Campaign",
        "description": "Choose this option to let the AI Dungeon Master generate a unique campaign based on your input. Leave this blank to let the Dungeon Master choose for you.",
        "themes": ["Varies", "Player-Driven"],
        "estimated_length": "Varies",
        "leveling": "Milestone (typically)",
        "is_default": True
    }
    campaigns.append(default_campaign)

    world_campaign_dir = os.path.join(CAMPAIGNS_DIR, world_id)
    current_app.logger.info(f"Attempting to load campaigns for world '{world_id}' from: {world_campaign_dir}")

    try:
        if not os.path.exists(CAMPAIGNS_DIR):
            current_app.logger.warning(f"Root campaigns directory not found: {CAMPAIGNS_DIR}")
            return jsonify({"success": True, "campaigns": campaigns}) # Return default only

        if not os.path.isdir(world_campaign_dir): # Check if it's a directory
            current_app.logger.info(f"No campaign directory found for world: {world_id}. Returning default campaign.")
            return jsonify({"success": True, "campaigns": campaigns}) # Return default only

        try:
            files_in_dir = os.listdir(world_campaign_dir)
            current_app.logger.info(f"Files found: {files_in_dir}")
        except Exception as list_err:
            current_app.logger.error(f"Error listing files in directory {world_campaign_dir}: {list_err}")
            return jsonify({"success": True, "Campaigns" : campaigns})
        
        for filename in os.listdir(world_campaign_dir):
            if filename.endswith((".yaml", ".yml")):
                
                current_app.logger.debug(f"Found potential campaign file: {filename}")
                file_path = os.path.join(world_campaign_dir, filename)
                current_app.logger.debug(f"Processing campaign file: {filename}")
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        campaign_data = yaml.safe_load(f)
                        if not campaign_data:
                            current_app.logger.warning(f"Campaign file {filename} is empty or invalid YAML.")
                            continue

                        # Basic validation
                        if not all(k in campaign_data for k in ['id', 'name', 'description']):
                            current_app.logger.warning(f"Campaign file {filename} missing required fields (id, name, description). Skipping.")
                            continue

                        # Construct campaign dict
                        loaded_campaign = {
                            "id": campaign_data.get("id"),
                            "name": campaign_data.get("name"),
                            "description": campaign_data.get("description"),
                            "themes": campaign_data.get("themes", ["Adventure"]),
                            "estimated_length": campaign_data.get("estimated_length", "Medium"),
                            "leveling": campaign_data.get("leveling", "Milestone"),
                            "image": campaign_data.get("image"), # Handle image path later if needed
                            "is_default": False
                        }

                        if loaded_campaign["image"]:
                            image_path = loaded_campaign["image"]
                            if image_path.startswith('/') and not image_path.startswith('http'):
                                full_image_url = f"{VITE_BASE_URL}{image_path}"
                                loaded_campaign
                                current_app.logger.debug(f"Constructed full image URL: {full_image_url}")
                            elif image_path:
                                loaded_campaign["image"] = image_path.strip('\'"')

                            
                        campaigns.append(loaded_campaign)
                        current_app.logger.debug(f"Successfully loaded campaign: {campaign_data.get('name')}")

                except yaml.YAMLError as e:
                    # Log YAML parsing errors specifically
                    current_app.logger.error(f"Error parsing YAML file {filename}: {e}", exc_info=True)
                    # Optionally continue to next file or return error depending on desired behavior
                    continue # Continue to try loading other files
                except FileNotFoundError:
                     current_app.logger.error(f"Campaign file not found during iteration (unexpected): {file_path}")
                     continue # Continue to try loading other files
                except Exception as e:
                    # Log other errors during file processing
                    current_app.logger.error(f"Error loading campaign file {filename}: {e}", exc_info=True)
                    continue # Continue to try loading other files

        current_app.logger.info(f"Successfully loaded {len(campaigns) - 1} campaigns from directory for world {world_id}")
        return jsonify({"success": True, "campaigns": campaigns})

    except Exception as e:
        # Log any errors occurring during directory listing or path manipulation
        current_app.logger.error(f"General error reading campaigns directory {world_campaign_dir}: {e}", exc_info=True)
        # Return only the default option in case of a significant error
        # Using 500 status code as the frontend received it
        return jsonify({"success": False, "error": f"Failed to retrieve campaigns for world {world_id}.", "details": str(e)}), 500


def load_data_from_file(file_path):
    """Helper to load YAML data from a file."""
    try:
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        current_app.logger.error(f"Error loading data file {file_path}: {e}")
        return None

@characters_bp.route('/api/creation-data/<world_id>', methods=['GET'])
@login_required
def get_world_data():
    """API endpoint to get filtered creation data (classes, races, etc.) for a world."""
    try:
        # 1. Load the main world definition file to see what's allowed
        world_file = os.path.join(WORLDS_DIR, f"{world_id}.yaml") # Assuming file name matches world_id
        if not os.path.exists(world_file):
             world_file = os.path.join(WORLDS_DIR, f"{world_id}.yml") # Try .yml extension
             if not os.path.exists(world_file):
                return jsonify({"success": False, "error": f"World definition '{world_id}' not found."}), 404
                
        world_definition = load_data_from_file(world_file)
        if not world_definition:
             return jsonify({"success": False, "error": f"Could not load world definition '{world_id}'."}), 500

        allowed_classes_ids = world_definition.get("allowed_classes", [])
        allowed_races_ids = world_definition.get("allowed_races", [])
        allowed_backgrounds_ids = world_definition.get("allowed_backgrounds", [])
        # Add allowed spells, equipment packs etc.

        # 2. Load the actual data for allowed items
        world_specific_data = {
            "classes": [],
            "races": [],
            "backgrounds": []
            # Add spells, equipment etc.
        }

        # Load Classes
        for class_id in allowed_classes_ids:
            # Check for world-specific class file first, then common
            class_file = os.path.join(CLASSES_DIR, world_id, f"{class_id}.yaml")
            if not os.path.exists(class_file):
                 class_file = os.path.join(CLASSES_DIR, world_id, f"{class_id}.yml")
            if not os.path.exists(class_file):
                class_file = os.path.join(CLASSES_DIR, 'common', f"{class_id}.yaml")
            if not os.path.exists(class_file):
                 class_file = os.path.join(CLASSES_DIR, 'common', f"{class_id}.yml")
                 
            class_data = load_data_from_file(class_file)
            if class_data:
                 world_specific_data["classes"].append(class_data)

        # Load Races (similar logic for world-specific vs common)
        for race_id in allowed_races_ids:
            race_file = os.path.join(RACES_DIR, world_id, f"{race_id}.yaml") # Check world specific first
            if not os.path.exists(race_file):
                race_file = os.path.join(RACES_DIR, world_id, f"{race_id}.yml")
            if not os.path.exists(race_file):
                 race_file = os.path.join(RACES_DIR, 'common', f"{race_id}.yaml") # Fallback to common
            if not os.path.exists(race_file):
                race_file = os.path.join(RACES_DIR, 'common', f"{race_id}.yml")

            race_data = load_data_from_file(race_file)
            if race_data:
                world_specific_data["races"].append(race_data)

        # Load Backgrounds (similar logic)
        for bg_id in allowed_backgrounds_ids:
            bg_file = os.path.join(BACKGROUNDS_DIR, world_id, f"{bg_id}.yaml") # Check world specific first
            if not os.path.exists(bg_file):
                 bg_file = os.path.join(BACKGROUNDS_DIR, world_id, f"{bg_id}.yml")
            if not os.path.exists(bg_file):
                bg_file = os.path.join(BACKGROUNDS_DIR, 'common', f"{bg_id}.yaml") # Fallback to common
            if not os.path.exists(bg_file):
                bg_file = os.path.join(BACKGROUNDS_DIR, 'common', f"{bg_id}.yml")

            bg_data = load_data_from_file(bg_file)
            if bg_data:
                world_specific_data["backgrounds"].append(bg_data)

        # --- TODO: Add similar loading logic for spells, equipment packs etc. ---

        return jsonify({"success": True, "data": world_specific_data})

    except Exception as e:
        current_app.logger.error(f"Error getting creation data for world {world_id}: {e}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": "Failed to retrieve creation data."}), 500

@characters_bp.route('/api/campaigns/generate', methods=['POST'])
@login_required
def generate_campaign():
    pass

