# =============================================================================
# app/infrastructure/ai/processors/story_processor.py
# =============================================================================
import logging
from typing import Any, Dict, List, Optional

from app.domain.models.character import CharacterAppearance, CharacterPersonality
from app.domain.models.scene import SceneEnvironment, TimeOfDay
from app.infrastructure.ai.llm.base import BaseLLMClient, ChatMessage, MessageRole

logger = logging.getLogger(__name__)


class StoryProcessor:
    """Processes story generation and scene creation using LLM."""

    def __init__(self, llm_client: BaseLLMClient):
        self.llm_client = llm_client

    async def generate_story_outline(
        self, prompt: str, style: str = "webtoon", target_panels: int = 6
    ) -> Dict[str, Any]:
        """Generate a complete story outline from a prompt."""
        try:
            system_message = """You are a professional webtoon writer. Create a compelling story outline 
            that can be adapted into visual panels. Focus on visual storytelling, character development, 
            and dramatic moments that work well in the webtoon format."""

            user_message = f"""
            Create a story outline for a {style} with approximately {target_panels} panels.
            
            Story prompt: {prompt}
            
            The outline should include:
            1. Title and genre
            2. Main characters (2-4 characters max)
            3. Setting and world
            4. Plot summary with 3-5 key scenes
            5. Emotional beats and character arcs
            6. Visual themes and mood
            """

            schema = {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "genre": {"type": "string"},
                    "target_audience": {"type": "string"},
                    "setting": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string"},
                            "time_period": {"type": "string"},
                            "description": {"type": "string"},
                        },
                    },
                    "characters": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "role": {"type": "string"},
                                "description": {"type": "string"},
                                "personality_traits": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "visual_description": {"type": "string"},
                            },
                        },
                    },
                    "plot_summary": {"type": "string"},
                    "key_scenes": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "description": {"type": "string"},
                                "characters_involved": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "emotional_beat": {"type": "string"},
                                "visual_focus": {"type": "string"},
                            },
                        },
                    },
                    "visual_themes": {"type": "array", "items": {"type": "string"}},
                    "mood": {"type": "string"},
                    "color_palette": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "title",
                    "genre",
                    "setting",
                    "characters",
                    "plot_summary",
                    "key_scenes",
                ],
            }

            result = await self.llm_client.generate_structured_output(
                user_message, schema, temperature=0.8
            )

            logger.info(f"Generated story outline: {result['title']}")
            return result

        except Exception as e:
            logger.error(f"Story generation error: {str(e)}")
            raise

    async def expand_characters(self, characters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Expand character descriptions with detailed appearance and personality."""
        expanded_characters = []

        for char in characters:
            try:
                prompt = f"""
                Expand this character for a webtoon:
                Name: {char['name']}
                Role: {char['role']}
                Description: {char['description']}
                
                Provide detailed appearance and personality information suitable for consistent visual representation.
                """

                schema = {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "role": {"type": "string"},
                        "description": {"type": "string"},
                        "appearance": {
                            "type": "object",
                            "properties": {
                                "age_range": {
                                    "type": "string",
                                    "enum": ["child", "teen", "young_adult", "adult", "elderly"],
                                },
                                "gender": {"type": "string"},
                                "height": {"type": "string", "enum": ["short", "average", "tall"]},
                                "build": {
                                    "type": "string",
                                    "enum": ["slim", "average", "muscular", "heavy"],
                                },
                                "hair_color": {"type": "string"},
                                "hair_style": {"type": "string"},
                                "eye_color": {"type": "string"},
                                "skin_tone": {"type": "string"},
                                "distinctive_features": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                            },
                        },
                        "personality": {
                            "type": "object",
                            "properties": {
                                "traits": {"type": "array", "items": {"type": "string"}},
                                "motivations": {"type": "array", "items": {"type": "string"}},
                                "fears": {"type": "array", "items": {"type": "string"}},
                                "speech_style": {
                                    "type": "string",
                                    "enum": ["formal", "casual", "rough", "elegant", "normal"],
                                },
                            },
                        },
                    },
                }

                expanded = await self.llm_client.generate_structured_output(
                    prompt, schema, temperature=0.5
                )

                expanded_characters.append(expanded)

            except Exception as e:
                logger.error(f"Character expansion error for {char['name']}: {str(e)}")
                # Fallback to original character data
                expanded_characters.append(char)

        return expanded_characters

    async def generate_scene_descriptions(
        self, story_outline: Dict[str, Any], target_panels: int
    ) -> List[Dict[str, Any]]:
        """Generate detailed scene descriptions for panels."""
        try:
            prompt = f"""
            Based on this story outline, create {target_panels} detailed scene descriptions for webtoon panels:
            
            Title: {story_outline['title']}
            Plot: {story_outline['plot_summary']}
            Characters: {[char['name'] for char in story_outline['characters']]}
            Key Scenes: {story_outline['key_scenes']}
            
            Each panel should:
            1. Advance the story meaningfully
            2. Have clear visual composition
            3. Include character positions and expressions
            4. Specify dialogue and speech bubble placement
            5. Set the mood and atmosphere
            """

            schema = {
                "type": "object",
                "properties": {
                    "scenes": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "panel_number": {"type": "integer"},
                                "title": {"type": "string"},
                                "description": {"type": "string"},
                                "environment": {
                                    "type": "object",
                                    "properties": {
                                        "location": {"type": "string"},
                                        "time_of_day": {
                                            "type": "string",
                                            "enum": [
                                                "dawn",
                                                "morning",
                                                "noon",
                                                "afternoon",
                                                "dusk",
                                                "night",
                                            ],
                                        },
                                        "weather": {"type": "string"},
                                        "lighting": {
                                            "type": "string",
                                            "enum": ["natural", "dramatic", "soft", "harsh"],
                                        },
                                        "atmosphere": {
                                            "type": "string",
                                            "enum": [
                                                "tense",
                                                "peaceful",
                                                "chaotic",
                                                "romantic",
                                                "neutral",
                                            ],
                                        },
                                    },
                                },
                                "characters_present": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "character_positions": {"type": "string"},
                                "dialogue": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "character": {"type": "string"},
                                            "text": {"type": "string"},
                                            "emotion": {"type": "string"},
                                            "style": {
                                                "type": "string",
                                                "enum": [
                                                    "normal",
                                                    "whisper",
                                                    "shout",
                                                    "thought",
                                                    "narration",
                                                ],
                                            },
                                        },
                                    },
                                },
                                "camera_angle": {
                                    "type": "string",
                                    "enum": ["close_up", "medium", "wide", "extreme_wide"],
                                },
                                "visual_focus": {"type": "string"},
                                "special_effects": {"type": "array", "items": {"type": "string"}},
                                "emotional_beat": {"type": "string"},
                            },
                        },
                    }
                },
            }

            result = await self.llm_client.generate_structured_output(
                prompt, schema, temperature=0.7
            )

            logger.info(f"Generated {len(result['scenes'])} scene descriptions")
            return result["scenes"]

        except Exception as e:
            logger.error(f"Scene generation error: {str(e)}")
            raise
