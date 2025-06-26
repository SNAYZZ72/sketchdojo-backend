"""
WebSocket tools for webtoon manipulation
"""
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.infrastructure.notifications.notification_types import NotificationType
from app.infrastructure.notifications.redis_publisher import get_redis_publisher

from app.websocket.handlers.tool_handler import Tool
from app.application.services.generation_service import GenerationService
from app.application.services.webtoon_service import WebtoonService
from app.application.dto.generation_dto import GenerationRequestDTO
from app.domain.entities.character import Character, CharacterAppearance
from app.domain.constants.art_styles import ensure_art_style_string

logger = logging.getLogger(__name__)


class CreatePanelTool(Tool):
    """Tool to create a new panel in a webtoon"""
    
    def __init__(self, generation_service: GenerationService, webtoon_service: WebtoonService):
        super().__init__(
            tool_id="create_panel",
            name="Create Panel",
            description="Create a new panel for the webtoon with specified scene description",
            parameters={
                "type": "object",
                "properties": {
                    "webtoon_id": {
                        "type": "string",
                        "description": "The ID of the webtoon to add the panel to"
                    },
                    "scene_description": {
                        "type": "string",
                        "description": "Description of the scene to generate"
                    },
                    "art_style": {
                        "type": "string",
                        "description": "Art style for the panel",
                        "default": "webtoon"
                    },
                    "character_names": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Names of characters in the scene"
                    },
                    "mood": {
                        "type": "string",
                        "description": "Mood of the scene (e.g., happy, sad, tense)",
                        "default": "neutral"
                    },
                    "task_id": {
                        "type": "string",
                        "description": "The ID of the task to associate with this operation for notifications"
                    }
                },
                "required": ["webtoon_id", "scene_description"]
            }
        )
        self.generation_service = generation_service
        self.webtoon_service = webtoon_service
    
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        webtoon_id = parameters.get("webtoon_id")
        scene_description = parameters.get("scene_description")
        art_style = ensure_art_style_string(parameters.get("art_style", "webtoon"))
        character_names = parameters.get("character_names", [])
        mood = parameters.get("mood", "neutral")
        task_id = parameters.get("task_id", str(UUID()))
        
        # Start panel generation
        result_dto = await self.generation_service.start_panel_generation(
            scene_description=scene_description,
            art_style=art_style,
            character_names=character_names,
            panel_size="medium",
            mood=mood
        )
        
        # After successfully initiating panel generation, fetch the current webtoon HTML
        # to provide an immediate update to the client via Redis
        try:
            # Get notification publisher
            notification_publisher = get_redis_publisher()
            
            # Fetch current HTML content
            html_content = await self.webtoon_service.get_webtoon_html_content(UUID(webtoon_id))
            
            # Publish update if HTML content is available
            if html_content:
                notification_publisher.publish(
                    NotificationType.WEBTOON_UPDATED,
                    {
                        "task_id": task_id,
                        "webtoon_id": webtoon_id,
                        "html_content": html_content
                    }
                )
                
        except Exception as e:
            logging.error(f"Error sending webtoon HTML update: {str(e)}")
        
        # Return information about the initiated task
        return {
            "task_id": str(result_dto.task_id),
            "status": result_dto.status,
            "message": "Panel generation started successfully",
            "webtoon_id": webtoon_id
        }


class EditPanelTool(Tool):
    """Tool to edit an existing panel in a webtoon"""
    
    def __init__(self, generation_service: GenerationService, webtoon_service: WebtoonService):
        super().__init__(
            tool_id="edit_panel",
            name="Edit Panel",
            description="Edit an existing panel in the webtoon",
            parameters={
                "type": "object",
                "properties": {
                    "webtoon_id": {
                        "type": "string",
                        "description": "The ID of the webtoon containing the panel"
                    },
                    "panel_id": {
                        "type": "string",
                        "description": "The ID of the panel to edit"
                    },
                    "new_scene_description": {
                        "type": "string",
                        "description": "New description for the scene (optional)"
                    },
                    "art_style": {
                        "type": "string",
                        "description": "New art style for the panel (optional)"
                    },
                    "regenerate": {
                        "type": "boolean",
                        "description": "Whether to regenerate the panel image",
                        "default": False
                    },
                    "task_id": {
                        "type": "string",
                        "description": "The ID of the task to associate with this operation for notifications"
                    }
                },
                "required": ["webtoon_id", "panel_id"]
            }
        )
        self.generation_service = generation_service
        self.webtoon_service = webtoon_service
    
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        webtoon_id = parameters.get("webtoon_id")
        panel_id = parameters.get("panel_id")
        new_scene_description = parameters.get("new_scene_description")
        art_style = parameters.get("art_style")
        regenerate = parameters.get("regenerate", False)
        task_id = parameters.get("task_id", str(UUID()))
        
        # Get the existing panel
        webtoon = await self.webtoon_service.get_webtoon(UUID(webtoon_id))
        if not webtoon:
            raise ValueError(f"Webtoon with ID {webtoon_id} not found")
        
        # Find the panel to edit
        panel = None
        for p in webtoon.panels:
            if str(p.id) == panel_id:
                panel = p
                break
        
        if not panel:
            raise ValueError(f"Panel with ID {panel_id} not found in webtoon {webtoon_id}")
        
        # Update panel properties
        updated = False
        if new_scene_description:
            # Update panel metadata
            panel.description = new_scene_description
            updated = True
        
        if art_style:
            # Update art style
            panel.art_style = ensure_art_style_string(art_style)
            updated = True
            
        # Update the panel in the database
        if updated:
            await self.webtoon_service.update_panel(
                webtoon_id=UUID(webtoon_id),
                panel_id=UUID(panel_id),
                updated_panel=panel
            )
            
        # Regenerate panel if requested
        task_id = None
        if regenerate:
            # Get character names from the webtoon
            character_names = [c.name for c in webtoon.characters]
            
            # Start panel regeneration
            result_dto = await self.generation_service.start_panel_generation(
                scene_description=panel.description,
                art_style=panel.art_style,
                character_names=character_names,
                panel_size="medium",
                mood=panel.mood or "neutral"
            )
            task_id = str(result_dto.task_id)
        
        # After successfully updating panel, fetch the current webtoon HTML
        try:
            # Get notification publisher
            notification_publisher = get_redis_publisher()
            
            # Fetch current HTML content
            html_content = await self.webtoon_service.get_webtoon_html_content(UUID(webtoon_id))
            
            # Publish update if HTML content is available
            if html_content:
                notification_publisher.publish(
                    NotificationType.WEBTOON_UPDATED,
                    {
                        "task_id": task_id,
                        "webtoon_id": webtoon_id,
                        "html_content": html_content
                    }
                )
                
        except Exception as e:
            logging.error(f"Error sending webtoon HTML update: {str(e)}")
        
        # Return results
        return {
            "webtoon_id": webtoon_id,
            "panel_id": panel_id,
            "updated": updated,
            "regenerated": regenerate,
            "task_id": task_id,
            "message": "Panel updated successfully"
        }


class RemovePanelTool(Tool):
    """Tool to remove a panel from a webtoon"""
    
    def __init__(self, webtoon_service: WebtoonService):
        super().__init__(
            tool_id="remove_panel",
            name="Remove Panel",
            description="Remove a panel from the webtoon",
            parameters={
                "type": "object",
                "properties": {
                    "webtoon_id": {
                        "type": "string",
                        "description": "The ID of the webtoon containing the panel"
                    },
                    "panel_id": {
                        "type": "string",
                        "description": "The ID of the panel to remove"
                    },
                    "task_id": {
                        "type": "string",
                        "description": "The ID of the task to associate with this operation for notifications"
                    }
                },
                "required": ["webtoon_id", "panel_id"]
            }
        )
        self.webtoon_service = webtoon_service
    
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        webtoon_id = parameters.get("webtoon_id")
        panel_id = parameters.get("panel_id")
        task_id = parameters.get("task_id", str(UUID()))
        
        # Remove the panel
        result = await self.webtoon_service.remove_panel(
            webtoon_id=UUID(webtoon_id),
            panel_id=UUID(panel_id)
        )
        
        if not result:
            raise ValueError(f"Failed to remove panel {panel_id} from webtoon {webtoon_id}")
        
        # After successfully removing panel, fetch the current webtoon HTML
        try:
            # Get notification publisher
            notification_publisher = get_redis_publisher()
            
            # Fetch current HTML content
            html_content = await self.webtoon_service.get_webtoon_html_content(UUID(webtoon_id))
            
            # Publish update if HTML content is available
            if html_content:
                notification_publisher.publish(
                    NotificationType.WEBTOON_UPDATED,
                    {
                        "task_id": task_id,
                        "webtoon_id": webtoon_id,
                        "html_content": html_content
                    }
                )
                
        except Exception as e:
            logging.error(f"Error sending webtoon HTML update: {str(e)}")
            
        return {
            "webtoon_id": webtoon_id,
            "panel_id": panel_id,
            "message": "Panel removed successfully"
        }


class AddCharacterTool(Tool):
    """Tool to add a character to a webtoon"""
    
    def __init__(self, webtoon_service: WebtoonService):
        super().__init__(
            tool_id="add_character",
            name="Add Character",
            description="Add a new character to the webtoon",
            parameters={
                "type": "object",
                "properties": {
                    "webtoon_id": {
                        "type": "string",
                        "description": "The ID of the webtoon to add the character to"
                    },
                    "name": {
                        "type": "string",
                        "description": "Name of the character"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of the character"
                    },
                    "appearance": {
                        "type": "object",
                        "properties": {
                            "hair_color": {"type": "string"},
                            "eye_color": {"type": "string"},
                            "skin_tone": {"type": "string"},
                            "clothing": {"type": "string"},
                            "height": {"type": "string"},
                            "build": {"type": "string"}
                        },
                        "description": "Character's physical appearance"
                    },
                    "personality_traits": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Character's personality traits"
                    },
                    "role": {
                        "type": "string",
                        "description": "Character's role in the story"
                    },
                    "task_id": {
                        "type": "string",
                        "description": "The ID of the task to associate with this operation for notifications"
                    }
                },
                "required": ["webtoon_id", "name", "description"]
            }
        )
        self.webtoon_service = webtoon_service
    
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        webtoon_id = parameters.get("webtoon_id")
        name = parameters.get("name")
        description = parameters.get("description")
        appearance = parameters.get("appearance", {})
        personality_traits = parameters.get("personality_traits", [])
        role = parameters.get("role", "")
        task_id = parameters.get("task_id", str(UUID()))
        
        # Create character entity
        character = Character(
            name=name,
            description=description,
            appearance=CharacterAppearance(**appearance),
            personality_traits=personality_traits,
            role=role
        )
        
        # Add character to the webtoon
        result = await self.webtoon_service.add_character(
            webtoon_id=UUID(webtoon_id),
            character=character
        )
        
        if not result:
            raise ValueError(f"Failed to add character to webtoon {webtoon_id}")
        
        # After successfully adding character, fetch the current webtoon HTML
        try:
            # Get notification publisher
            notification_publisher = get_redis_publisher()
            
            # Fetch current HTML content
            html_content = await self.webtoon_service.get_webtoon_html_content(UUID(webtoon_id))
            
            # Publish update if HTML content is available
            if html_content:
                notification_publisher.publish(
                    NotificationType.WEBTOON_UPDATED,
                    {
                        "task_id": task_id,
                        "webtoon_id": webtoon_id,
                        "html_content": html_content
                    }
                )
                
        except Exception as e:
            logging.error(f"Error sending webtoon HTML update: {str(e)}")
            
        return {
            "webtoon_id": webtoon_id,
            "character_name": name,
            "message": f"Character '{name}' added successfully"
        }


class AddSpeechBubbleTool(Tool):
    """Tool to add a speech bubble to a panel"""
    
    def __init__(self, webtoon_service: WebtoonService):
        super().__init__(
            tool_id="add_speech_bubble",
            name="Add Speech Bubble",
            description="Add a speech bubble to a panel in the webtoon",
            parameters={
                "type": "object",
                "properties": {
                    "webtoon_id": {
                        "type": "string",
                        "description": "The ID of the webtoon containing the panel"
                    },
                    "panel_id": {
                        "type": "string",
                        "description": "The ID of the panel to add the speech bubble to"
                    },
                    "character_name": {
                        "type": "string",
                        "description": "Name of the character speaking"
                    },
                    "text": {
                        "type": "string",
                        "description": "The text content of the speech bubble"
                    },
                    "bubble_type": {
                        "type": "string",
                        "description": "Type of speech bubble (speech, thought, narration)",
                        "enum": ["speech", "thought", "narration"],
                        "default": "speech"
                    },
                    "position": {
                        "type": "string",
                        "description": "Position of the bubble in the panel",
                        "enum": ["top-left", "top-right", "bottom-left", "bottom-right", "center"],
                        "default": "top-right"
                    },
                    "task_id": {
                        "type": "string",
                        "description": "The ID of the task to associate with this operation for notifications"
                    }
                },
                "required": ["webtoon_id", "panel_id", "text"]
            }
        )
        self.webtoon_service = webtoon_service
    
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        webtoon_id = parameters.get("webtoon_id")
        panel_id = parameters.get("panel_id")
        character_name = parameters.get("character_name")
        text = parameters.get("text")
        bubble_type = parameters.get("bubble_type", "speech")
        position = parameters.get("position", "top-right")
        task_id = parameters.get("task_id", str(UUID()))
        
        # Add speech bubble to the panel
        result = await self.webtoon_service.add_speech_bubble(
            webtoon_id=UUID(webtoon_id),
            panel_id=UUID(panel_id),
            character_name=character_name,
            text=text,
            bubble_type=bubble_type,
            position=position
        )
        
        if not result:
            raise ValueError(f"Failed to add speech bubble to panel {panel_id}")
        
        # After successfully adding speech bubble, fetch the current webtoon HTML
        try:
            # Get notification publisher
            notification_publisher = get_redis_publisher()
            
            # Fetch current HTML content
            html_content = await self.webtoon_service.get_webtoon_html_content(UUID(webtoon_id))
            
            # Publish update if HTML content is available
            if html_content:
                notification_publisher.publish(
                    NotificationType.WEBTOON_UPDATED,
                    {
                        "task_id": task_id,
                        "webtoon_id": webtoon_id,
                        "html_content": html_content
                    }
                )
                
        except Exception as e:
            logging.error(f"Error sending webtoon HTML update: {str(e)}")
            
        return {
            "webtoon_id": webtoon_id,
            "panel_id": panel_id,
            "character_name": character_name,
            "message": "Speech bubble added successfully"
        }


# Utility function to register all webtoon tools
def register_webtoon_tools(
    tool_handler,
    generation_service: GenerationService,
    webtoon_service: WebtoonService
) -> None:
    """Register all webtoon manipulation tools with the tool handler"""
    tools = [
        CreatePanelTool(generation_service, webtoon_service),
        EditPanelTool(generation_service, webtoon_service),
        RemovePanelTool(webtoon_service),
        AddCharacterTool(webtoon_service),
        AddSpeechBubbleTool(webtoon_service)
    ]
    
    for tool in tools:
        tool_handler.register_tool(tool)
        logger.info(f"Registered webtoon tool: {tool.name}")
