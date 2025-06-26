# app/application/services/character_service.py
"""
Character management service for generating and managing characters in the webtoon.
"""
import logging
from typing import Any, Dict, List, Optional

from app.application.interfaces.ai_provider import AIProvider
from app.application.services.base_service import BaseService
from app.core.error_handling.base_error_handler import BaseErrorHandler
from app.domain.entities.character import Character, CharacterAppearance


class CharacterService(BaseService):
    """
    Service for character management and generation.
    
    This service handles the creation, enhancement, and validation of characters
    within the webtoon system, including AI-powered character generation.
    """

    def __init__(
        self, 
        ai_provider: AIProvider,
        error_handler: Optional[BaseErrorHandler] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the character service.
        
        Args:
            ai_provider: The AI provider for character generation
            error_handler: Optional error handler instance
            logger: Optional logger instance
        """
        # Initialize with the provided logger or create a new one
        super().__init__(error_handler=error_handler, logger=logger or logging.getLogger(__name__))
        self.ai_provider = ai_provider

    async def generate_character_from_description(
        self, name: str, description: str, role: str = "character"
    ) -> Character:
        """
        Generate a detailed character from a basic description.
        
        Args:
            name: The character's name
            description: Basic description of the character
            role: The character's role in the story (default: "character")
            
        Returns:
            Character: A fully populated Character object
            
        Raises:
            ValueError: If character generation fails and cannot fall back to basic
        """
        context = {"character_name": name, "role": role, "description": description}
        
        try:
            self.logger.info(
                f"Generating enhanced character details for '{name}' (Role: {role})"
            )
            
            # Use AI to expand character details
            enhanced_details = await self._enhance_character_details(
                name, description, role
            )

            # Create appearance from details
            appearance = self._parse_appearance(enhanced_details.get("appearance", {}))

            # Create character
            character = Character(
                name=name,
                description=enhanced_details.get("description", description),
                appearance=appearance,
                personality_traits=enhanced_details.get("personality_traits", []),
                role=role,
                backstory=enhanced_details.get("backstory", ""),
                goals=enhanced_details.get("goals", []),
            )
            
            self.logger.debug(f"Successfully generated character: {name}")
            return character

        except Exception as e:
            error_msg = f"Error generating enhanced character '{name}': {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            
            # Only fall back to basic character for certain error types
            if isinstance(e, (ValueError, AttributeError)):
                self.logger.warning("Falling back to basic character creation")
                return Character(name=name, description=description, role=role)
                
            # For other errors, use the error handler and re-raise
            self.handle_error(e, context=context)
            raise

    async def _enhance_character_details(
        self, name: str, description: str, role: str
    ) -> Dict[str, Any]:
        """
        Use AI to enhance character details.
        
        Args:
            name: Character's name
            description: Basic character description
            role: Character's role in the story
            
        Returns:
            Dict containing enhanced character details
            
        Raises:
            RuntimeError: If AI provider fails to generate details
        """
        try:
            self.logger.debug(
                f"Enhancing character details for '{name}' with role '{role}'"
            )
            
            # In a real implementation, this would call the AI provider
            # For now, return a basic structure
            enhanced_details = {
                "description": description,
                "appearance": {
                    "height": "average",
                    "build": "normal",
                    "hair_color": "brown",
                    "eye_color": "brown",
                    "hair_style": "straight",
                    "skin_tone": "fair",
                    "distinctive_features": [],
                    "clothing_style": "casual"
                },
                "personality_traits": ["determined", "brave"],
                "backstory": f"{name} is a {role} in this story.",
                "goals": ["Complete their mission"],
            }
            
            self.logger.debug("Successfully enhanced character details")
            return enhanced_details
            
        except Exception as e:
            error_msg = f"Failed to enhance character details: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg) from e

    def _parse_appearance(self, appearance_data: Dict[str, Any]) -> CharacterAppearance:
        """
        Parse appearance data into a CharacterAppearance object.
        
        Args:
            appearance_data: Dictionary containing appearance attributes
            
        Returns:
            CharacterAppearance: Populated appearance object
            
        Raises:
            ValueError: If required appearance data is missing or invalid
        """
        try:
            self.logger.debug("Parsing character appearance data")
            
            if not appearance_data:
                raise ValueError("No appearance data provided")
                
            appearance = CharacterAppearance(
                height=appearance_data.get("height", ""),
                build=appearance_data.get("build", ""),
                hair_color=appearance_data.get("hair_color", ""),
                hair_style=appearance_data.get("hair_style", ""),
                eye_color=appearance_data.get("eye_color", ""),
                skin_tone=appearance_data.get("skin_tone", ""),
                distinctive_features=appearance_data.get("distinctive_features", []),
                clothing_style=appearance_data.get("clothing_style", ""),
            )
            
            return appearance
            
        except Exception as e:
            error_msg = f"Failed to parse appearance data: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise ValueError(error_msg) from e

    def validate_character_consistency(
        self, character: Character, scene_context: Dict[str, Any]
    ) -> List[str]:
        """
        Validate character consistency within the given scene context.
        
        Args:
            character: The character to validate
            scene_context: Dictionary containing scene context information
            
        Returns:
            List[str]: List of validation issues, empty if character is valid
        """
        issues = []
        
        try:
            self.logger.debug(
                f"Validating character '{character.name}' in scene context"
            )

            # Check if character name is present
            if not character.name or not character.name.strip():
                issues.append("Character must have a name")
                self.logger.warning("Character validation failed: Missing name")

            # Check role consistency
            if (
                character.role == "protagonist"
                and scene_context.get("scene_type") == "background"
                and not scene_context.get("protagonist_purpose")
            ):
                issue_msg = "Protagonist should not be in background scenes without purpose"
                issues.append(issue_msg)
                self.logger.warning(
                    f"Character validation warning for '{character.name}': {issue_msg}"
                )

            # Check appearance completeness for main characters
            if character.role in ["protagonist", "antagonist"]:
                if not character.appearance or not character.appearance.to_description():
                    issue_msg = f"Main character '{character.name}' lacks appearance details"
                    issues.append(issue_msg)
                    self.logger.warning(
                        f"Character validation warning for '{character.name}': {issue_msg}"
                    )
                    
            if not issues:
                self.logger.debug(
                    f"Character '{character.name}' passed all validation checks"
                )
                
            return issues
            
        except Exception as e:
            error_msg = f"Error during character validation: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            # Return a generic validation error
            return ["An error occurred during character validation"]

    async def generate_character_relationships(
        self, characters: List[Character]
    ) -> Dict[str, Dict[str, str]]:
        """
        Generate relationships between a list of characters.
        
        Args:
            characters: List of characters to generate relationships for
            
        Returns:
            Dict mapping character names to their relationships with others
            
        Raises:
            ValueError: If the character list is empty or invalid
        """
        try:
            if not characters:
                raise ValueError("Cannot generate relationships: Empty character list")
                
            self.logger.info(
                f"Generating relationships between {len(characters)} characters"
            )
            
            relationships = {}
            character_names = [c.name for c in characters if c.name]
            
            if len(character_names) != len(set(character_names)):
                self.logger.warning("Duplicate character names found, which may affect relationship mapping")

            for character in characters:
                if not character.name:
                    self.logger.warning("Skipping character with no name in relationship generation")
                    continue
                    
                relationships[character.name] = {}

                for other_character in characters:
                    if character.id != other_character.id and other_character.name:
                        relationship = self._determine_relationship(
                            character, other_character
                        )
                        if relationship:
                            relationships[character.name][other_character.name] = relationship
                            self.logger.debug(
                                f"Established relationship: {character.name} -> "
                                f"{other_character.name} = {relationship}"
                            )
            
            self.logger.info("Successfully generated character relationships")
            return relationships
            
        except Exception as e:
            error_msg = f"Failed to generate character relationships: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.handle_error(e, context={"character_count": len(characters) if characters else 0})
            raise

    def _determine_relationship(
        self, char1: Character, char2: Character
    ) -> Optional[str]:
        """
        Determine the relationship between two characters based on their roles.
        
        Args:
            char1: First character
            char2: Second character
            
        Returns:
            Optional[str]: The relationship type, or None if no specific relationship
            
        Note:
            This is a simplified implementation. In a production system, this would
            likely involve more complex relationship mapping and potentially AI analysis.
        """
        try:
            if not char1.role or not char2.role:
                self.logger.debug(
                    f"Cannot determine relationship: Missing role for {char1.name or 'Character 1'} "
                    f"or {char2.name or 'Character 2'}"
                )
                return None
                
            role_relationships = {
                ("protagonist", "antagonist"): "enemy",
                ("antagonist", "protagonist"): "enemy",
                ("protagonist", "supporting"): "ally",
                ("supporting", "protagonist"): "supports",
                ("protagonist", "love_interest"): "romantic",
                ("love_interest", "protagonist"): "romantic",
                ("supporting", "supporting"): "friend",
                ("mentor", "protagonist"): "mentor",
                ("protagonist", "mentor"): "student",
                ("sidekick", "protagonist"): "sidekick",
                ("protagonist", "sidekick"): "mentor"
            }

            relationship = role_relationships.get((char1.role.lower(), char2.role.lower()))
            
            if not relationship:
                self.logger.debug(
                    f"No specific relationship defined between {char1.role} "
                    f"and {char2.role} roles"
                )
                
            return relationship
            
        except Exception as e:
            self.logger.error(
                f"Error determining relationship between characters: {str(e)}",
                exc_info=True
            )
            return None


def get_character_service(
    ai_provider: AIProvider,
    error_handler: Optional[BaseErrorHandler] = None,
    logger: Optional[logging.Logger] = None
) -> CharacterService:
    """
    Factory function to create a CharacterService instance.
    
    Args:
        ai_provider: The AI provider for character generation
        error_handler: Optional error handler instance
        logger: Optional logger instance
        
    Returns:
        CharacterService: A configured instance of CharacterService
    """
    return CharacterService(
        ai_provider=ai_provider,
        error_handler=error_handler,
        logger=logger
    )
