"""
Data normalizers for AI responses
"""
import json
from typing import Any, Dict, List, Optional


class StoryDataNormalizer:
    """Normalizer for story generation data"""
    
    @staticmethod
    def normalize(data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize and validate story data"""
        normalized = {
            "title": data.get("title", "Generated Story"),
            "plot_summary": data.get("plot_summary", ""),
            "setting": data.get("setting", {}),
            "main_characters": data.get("main_characters", []),
            "theme": data.get("theme", "Adventure"),
            "mood": data.get("mood", "Balanced"),
            "key_scenes": data.get("key_scenes", []),
        }

        # Ensure main_characters is properly formatted
        characters = []
        for char in normalized["main_characters"]:
            if isinstance(char, dict):
                characters.append(
                    {
                        "name": char.get("name", "Character"),
                        "description": char.get("description", ""),
                        "role": char.get("role", "character"),
                    }
                )
            else:
                characters.append(
                    {"name": str(char), "description": "", "role": "character"}
                )
        normalized["main_characters"] = characters

        return normalized


class SceneDataNormalizer:
    """Normalizer for scene generation data"""
    
    @staticmethod
    def normalize(scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize and validate scenes data"""
        normalized_scenes = []

        for scene in scenes:
            normalized = {
                "visual_description": scene.get("visual_description", ""),
                "characters": scene.get("characters", []),
                "dialogue": scene.get("dialogue", []),
                "setting": scene.get("setting", ""),
                "mood": scene.get("mood", ""),
                "panel_size": scene.get("panel_size", "full"),
                "camera_angle": scene.get("camera_angle", "medium"),
                "special_effects": scene.get("special_effects", []),
            }

            # Ensure dialogue is properly formatted
            dialogue = []
            for d in normalized["dialogue"]:
                if isinstance(d, dict):
                    dialogue.append(
                        {
                            "character": d.get("character", "Character"),
                            "text": d.get("text", ""),
                        }
                    )
                else:
                    dialogue.append({"character": "Character", "text": str(d)})
            normalized["dialogue"] = dialogue

            normalized_scenes.append(normalized)

        return normalized_scenes


class DialogueDataNormalizer:
    """Normalizer for dialogue generation data"""
    
    @staticmethod
    def normalize(dialogue_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Normalize and validate dialogue data"""
        dialogue = dialogue_data.get("dialogue", [])
        normalized_dialogue = []
        
        for item in dialogue:
            if isinstance(item, dict):
                normalized_dialogue.append({
                    "character": item.get("character", "Character"),
                    "text": item.get("text", ""),
                })
            else:
                normalized_dialogue.append({
                    "character": "Character",
                    "text": str(item),
                })
                
        return normalized_dialogue
        

class ChatCompletionNormalizer:
    """Normalizer for chat completion data"""
    
    @staticmethod
    def normalize_response(response: Any) -> Dict[str, Any]:
        """Normalize OpenAI response to a standardized format"""
        result = {
            "content": response.choices[0].message.content,
            "finish_reason": response.choices[0].finish_reason,
        }
        
        # Add tool calls if present
        if hasattr(response.choices[0].message, "tool_calls") and response.choices[0].message.tool_calls:
            tool_calls = []
            for tool_call in response.choices[0].message.tool_calls:
                try:
                    arguments = json.loads(tool_call.function.arguments)
                except Exception:
                    # Fallback if JSON parsing fails
                    arguments = tool_call.function.arguments
                    
                tool_calls.append({
                    "id": tool_call.id,
                    "name": tool_call.function.name,
                    "arguments": arguments
                })
            result["tool_calls"] = tool_calls
            
        return result
