# app/infrastructure/ai/openai_provider.py
"""
OpenAI provider implementation
"""
import json
import logging
from typing import Any, Dict, List, Optional

import openai
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.application.interfaces.ai_provider import AIProvider
from app.infrastructure.ai.prompt_templates import PromptTemplates

logger = logging.getLogger(__name__)


class OpenAIProvider(AIProvider):
    """OpenAI implementation of AI provider interface"""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.templates = PromptTemplates()

        logger.info(f"Initialized OpenAI provider with model: {model}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def generate_story(
        self, prompt: str, style: str, additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a story structure from a prompt"""
        try:
            system_prompt = self.templates.get_story_generation_prompt(style)
            user_prompt = self.templates.format_story_request(
                prompt, additional_context
            )

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            story_data = json.loads(content)

            # Validate and normalize story data
            return self._normalize_story_data(story_data)

        except Exception as e:
            logger.error(f"Error generating story: {str(e)}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def generate_scene_descriptions(
        self, story: Dict[str, Any], num_panels: int
    ) -> List[Dict[str, Any]]:
        """Generate scene descriptions for panels"""
        try:
            system_prompt = self.templates.get_scene_generation_prompt()
            user_prompt = self.templates.format_scene_request(story, num_panels)

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            scenes_data = json.loads(content)

            # Validate and normalize scenes data
            return self._normalize_scenes_data(scenes_data.get("scenes", []))

        except Exception as e:
            logger.error(f"Error generating scenes: {str(e)}")
            raise

    async def generate_dialogue(
        self, scene_description: str, character_names: List[str], mood: str
    ) -> List[Dict[str, str]]:
        """Generate dialogue for characters in a scene"""
        try:
            system_prompt = self.templates.get_dialogue_generation_prompt()
            user_prompt = self.templates.format_dialogue_request(
                scene_description, character_names, mood
            )

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.temperature,
                max_tokens=1000,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            dialogue_data = json.loads(content)

            return dialogue_data.get("dialogue", [])

        except Exception as e:
            logger.error(f"Error generating dialogue: {str(e)}")
            return []

    async def enhance_visual_description(
        self, base_description: str, art_style: str, technical_specs: Dict[str, Any]
    ) -> str:
        """Enhance a visual description for image generation"""
        try:
            system_prompt = self.templates.get_visual_enhancement_prompt(art_style)
            user_prompt = self.templates.format_visual_enhancement_request(
                base_description, technical_specs
            )

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.8,  # Higher temperature for creative descriptions
                max_tokens=500,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Error enhancing visual description: {str(e)}")
            return base_description

    def _normalize_story_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
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

    def _normalize_scenes_data(
        self, scenes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Normalize and validate scenes data"""
        normalized_scenes = []

        for i, scene in enumerate(scenes):
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
