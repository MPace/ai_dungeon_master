import os
import requests
import json
from typing import Dict, List, Any, Optional

class AIHandler:
    """
    Handles communication with LLM API for generating D&D game responses
    """
    def __init__(self, api_url: str, api_key: str, model: str = None):
        self.api_url = api_url
        self.api_key = api_key
        self.model = model  # Store the model name
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
    def generate_response(self, 
                         player_message: str, 
                         conversation_history: List[Dict[str, Any]],
                         character_data: Optional[Dict[str, Any]] = None,
                         game_state: str = "intro") -> str:
        """
        Generate a response from the AI based on the player's message,
        conversation history, character data, and game state.
        
        Args:
            player_message: The message from the player
            conversation_history: List of previous messages in the conversation
            character_data: Optional character sheet data
            game_state: Current state of the game (intro, combat, exploration, etc.)
            
        Returns:
            The AI-generated response
        """
        try:
            # Format conversation history for the API
            formatted_history = self._format_conversation_history(conversation_history)
            
            # Create system prompt based on game state and character data
            system_prompt = self._create_system_prompt(game_state, character_data)
            
            # Prepare the request payload - adjusted for xAI/Grok API
            payload = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    *formatted_history,
                    {"role": "user", "content": player_message}
                ],
                "temperature": 0.7  # Add creativity but keep some consistency
            }
            
            # Add model to the payload if specified
            if self.model:
                payload["model"] = self.model
                
            # Add stream property, expected by xAI API
            payload["stream"] = False
            
            print(f"Sending request to LLM API: {self.api_url}")
            
            # Send request to the LLM API
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload
            )
            
            # Send request to the LLM API
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload
            )
            
            # Check if the request was successful
            response.raise_for_status()
            
            # Parse the response
            result = response.json()
            
            # Print response structure for debugging
            print(f"Response structure: {list(result.keys())}")
            
            # Extract the generated text based on API format
            if "choices" in result and len(result["choices"]) > 0:
                # OpenAI and xAI format
                if "message" in result["choices"][0]:
                    return result["choices"][0]["message"]["content"]
                elif "text" in result["choices"][0]:
                    return result["choices"][0]["text"]
            elif "generated_text" in result:
                # Some other APIs use this format
                return result["generated_text"]
            else:
                # Unknown format - log the full response and return a generic message
                print(f"Unknown response format: {result}")
                return "The Dungeon Master contemplates your action. (The AI response format is unrecognized)"
                
        except requests.exceptions.RequestException as e:
            print(f"Error communicating with LLM API: {e}")
            # For 422 errors, try to get more information from the response
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    print(f"API error details: {error_detail}")
                except:
                    print(f"Could not parse error response. Status code: {e.response.status_code}")
            return "The Dungeon Master seems to be taking a short break. Please try again in a moment."
        
        except Exception as e:
            print(f"Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return "The magical connection to the realm seems unstable. The Dungeon Master will return shortly."
    
    def _format_conversation_history(self, history: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Format conversation history to match API requirements"""
        formatted = []
        
        for entry in history[-10:]:  # Only use the last 10 messages to avoid context overflow
            role = "assistant" if entry["sender"] == "dm" else "user"
            formatted.append({
                "role": role,
                "content": entry["message"]
            })
            
        return formatted
    
    def _create_system_prompt(self, game_state: str, character_data: Optional[Dict[str, Any]]) -> str:
        """Create a system prompt based on the current game state and character data"""
        base_prompt = (
            "You are an expert Dungeon Master for a Dungeons & Dragons 5th Edition game. "
            "Create immersive, engaging responses that follow D&D 5e rules. "
            "Describe environments vividly, represent NPCs with distinct personalities, "
            "and keep the game flowing naturally. "
            "When rules or dice rolls are needed, mention them and incorporate the results into the narrative. "
        )
        
        # Add game state context
        if game_state == "intro":
            base_prompt += (
                "The player is just starting their adventure. Help them get oriented "
                "and excited about the campaign world. Offer hooks to engage them."
            )
        elif game_state == "combat":
            base_prompt += (
                "The player is in combat. Describe the action vividly and maintain tension. "
                "Track initiative order and enemy actions. Describe combat effects dramatically."
            )
        elif game_state == "exploration":
            base_prompt += (
                "The player is exploring. Describe the environment in rich detail. "
                "Include sensory information and interesting features that reward investigation."
            )
        elif game_state == "social":
            base_prompt += (
                "The player is in a social interaction. Portray NPCs with distinct personalities, "
                "motivations, and speech patterns. Respond to social approaches and charisma-based actions."
            )
        
        # Add character context if available
        if character_data:
            char_details = []
            if "name" in character_data:
                char_details.append(f"Name: {character_data['name']}")
            if "race" in character_data:
                char_details.append(f"Race: {character_data['race']}")
            if "class" in character_data:
                char_details.append(f"Class: {character_data['class']}")
            if "level" in character_data:
                char_details.append(f"Level: {character_data['level']}")
                
            if char_details:
                char_info = ", ".join(char_details)
                base_prompt += f"\n\nThe player's character is: {char_info}."
                
            # Add abilities if available
            if "abilities" in character_data:
                base_prompt += "\nCharacter ability scores: "
                for ability, score in character_data["abilities"].items():
                    base_prompt += f"{ability}: {score}, "
                    
        return base_prompt