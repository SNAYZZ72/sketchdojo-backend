# app/infrastructure/ai/prompt_templates.py
"""
Prompt templates for AI interactions
"""
from typing import Any, Dict, List, Optional


class PromptTemplates:
    """Collection of prompt templates for different AI tasks"""

    def get_story_generation_prompt(self, style: str) -> str:
        """Get system prompt for story generation"""
        return f"""
You are a professional {style} story writer. Your task is to create compelling story outlines that will be adapted into visual panels.

Generate a complete story structure with the following elements:
- title: A compelling title for the story
- plot_summary: A concise summary of the main plot
- setting: {{
    "location": "Where the story takes place",
    "time_period": "When the story takes place",
    "atmosphere": "Overall feel of the setting"
  }}
- main_characters: [
    {{
      "name": "Character name",
      "description": "Character description and appearance",
      "role": "protagonist/antagonist/supporting"
    }}
  ]
- theme: The main theme or message
- mood: Overall mood/tone of the story
- key_scenes: ["List of key visual moments for panels"]

Respond only with valid JSON following this exact structure.
"""

    def get_scene_generation_prompt(self) -> str:
        """Get system prompt for scene generation"""
        return """
You are a professional visual storyteller specializing in creating detailed scene descriptions for webtoon panels.

For each scene, provide:
- visual_description: Detailed description of what should be visually depicted
- characters: List of character names present in the scene
- dialogue: [{"character": "name", "text": "dialogue"}] format
- setting: Specific location/environment details
- mood: Emotional tone of the scene
- panel_size: "full", "half", "third", or "quarter"
- camera_angle: "close-up", "medium", "wide", "bird's-eye", etc.
- special_effects: ["List of visual effects like speed lines, etc."]

Focus on visual storytelling that works well in webtoon format.
Respond with JSON: {"scenes": [scene_objects]}
"""

    def get_dialogue_generation_prompt(self) -> str:
        """Get system prompt for dialogue generation"""
        return """
You are a professional dialogue writer for webtoons. Create natural, engaging dialogue that fits the scene and characters.

Consider:
- Character personalities and speaking patterns
- The emotional context of the scene
- Natural flow of conversation
- Appropriate length for speech bubbles

Respond with JSON: {"dialogue": [{"character": "name", "text": "dialogue"}]}
"""

    def get_visual_enhancement_prompt(self, art_style: str) -> str:
        """Get system prompt for visual description enhancement"""
        return f"""
You are a professional {art_style} artist. Enhance visual descriptions to be optimal for AI image generation.

Add specific details about:
- Art style characteristics ({art_style} specific elements)
- Lighting and atmosphere
- Color schemes and composition
- Technical artistic details
- Visual effects and stylistic elements

Create a detailed, technical description suitable for AI image generation while maintaining the core visual concept.
"""

    def format_story_request(
        self, prompt: str, additional_context: Optional[str]
    ) -> str:
        """Format a story generation request"""
        request = f"Create a story based on this prompt: {prompt}"
        if additional_context:
            request += f"\n\nAdditional context: {additional_context}"
        return request

    def format_scene_request(self, story: Dict[str, Any], num_panels: int) -> str:
        """Format a scene generation request"""
        return f"""
Based on this story outline, create {num_panels} detailed scene descriptions for webtoon panels:

Story: {story}

Create scenes that:
1. Follow the story's plot progression
2. Include key characters at appropriate moments
3. Vary in panel sizes and compositions for visual interest
4. Include natural dialogue that advances the story
5. Capture the story's mood and theme

Ensure scenes flow logically from one to the next and tell the complete story.
"""

    def format_dialogue_request(
        self, scene_description: str, character_names: List[str], mood: str
    ) -> str:
        """Format a dialogue generation request"""
        return f"""
Scene: {scene_description}
Characters present: {', '.join(character_names)}
Mood: {mood}

Generate appropriate dialogue for this scene that:
- Fits the characters and situation
- Matches the emotional mood
- Advances the story or reveals character
- Is suitable for webtoon speech bubbles
"""

    def format_visual_enhancement_request(
        self, base_description: str, technical_specs: Dict[str, Any]
    ) -> str:
        """Format a visual enhancement request"""
        specs_text = ", ".join([f"{k}: {v}" for k, v in technical_specs.items()])
        return f"""
Base description: {base_description}
Technical specifications: {specs_text}

Enhance this description for AI image generation, adding artistic and technical details while preserving the core visual concept.
"""
