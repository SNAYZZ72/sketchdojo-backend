# app/domain/repositories/webtoon_repository.py
"""
Webtoon repository implementation using storage provider
"""
import logging
from typing import List, Optional
from uuid import UUID

from app.application.interfaces.storage_provider import StorageProvider
from app.domain.entities.webtoon import Webtoon
from app.domain.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class WebtoonRepository(BaseRepository[Webtoon]):
    """Repository implementation for webtoon entities"""

    def __init__(self, storage: StorageProvider):
        self.storage = storage
        self.key_prefix = "webtoon:"
        logger.info("WebtoonRepository initialized")

    def _get_key(self, entity_id: UUID) -> str:
        """Get storage key for entity ID"""
        return f"{self.key_prefix}{str(entity_id)}"

    def _serialize_webtoon(self, webtoon: Webtoon) -> dict:
        """Serialize webtoon entity to dictionary"""
        return {
            "id": str(webtoon.id),
            "title": webtoon.title,
            "description": webtoon.description,
            "art_style": webtoon.art_style.value,
            "created_at": webtoon.created_at.isoformat(),
            "updated_at": webtoon.updated_at.isoformat(),
            "is_published": webtoon.is_published,
            "metadata": webtoon.metadata,
            "panels": [self._serialize_panel(panel) for panel in webtoon.panels],
            "characters": [
                self._serialize_character(char) for char in webtoon.characters
            ],
        }

    def _serialize_panel(self, panel) -> dict:
        """Serialize panel entity"""

        return {
            "id": str(panel.id),
            "sequence_number": panel.sequence_number,
            "scene": {
                "id": str(panel.scene.id),
                "description": panel.scene.description,
                "setting": panel.scene.setting,
                "time_of_day": panel.scene.time_of_day,
                "weather": panel.scene.weather,
                "mood": panel.scene.mood,
                "character_names": panel.scene.character_names,
                "character_positions": panel.scene.character_positions,
                "character_expressions": panel.scene.character_expressions,
                "actions": panel.scene.actions,
                "camera_angle": panel.scene.camera_angle,
                "lighting": panel.scene.lighting,
                "composition_notes": panel.scene.composition_notes,
            },
            "dimensions": {
                "size": panel.dimensions.size.value,
                "width": panel.dimensions.width,
                "height": panel.dimensions.height,
                "aspect_ratio": panel.dimensions.aspect_ratio,
            },
            "speech_bubbles": [
                {
                    "id": str(bubble.id),
                    "character_name": bubble.character_name,
                    "text": bubble.text,
                    "position": {
                        "x_percent": bubble.position.x_percent,
                        "y_percent": bubble.position.y_percent,
                        "anchor": bubble.position.anchor,
                    },
                    "style": bubble.style,
                    "tail_direction": bubble.tail_direction,
                }
                for bubble in panel.speech_bubbles
            ],
            "visual_effects": panel.visual_effects,
            "image_url": panel.image_url,
            "generated_at": panel.generated_at.isoformat()
            if panel.generated_at
            else None,
            "metadata": panel.metadata,
        }

    def _serialize_character(self, character) -> dict:
        """Serialize character entity"""
        return {
            "id": str(character.id),
            "name": character.name,
            "description": character.description,
            "appearance": {
                "height": character.appearance.height,
                "build": character.appearance.build,
                "hair_color": character.appearance.hair_color,
                "hair_style": character.appearance.hair_style,
                "eye_color": character.appearance.eye_color,
                "skin_tone": character.appearance.skin_tone,
                "distinctive_features": character.appearance.distinctive_features,
                "clothing_style": character.appearance.clothing_style,
            },
            "personality_traits": character.personality_traits,
            "role": character.role,
            "relationships": character.relationships,
            "backstory": character.backstory,
            "goals": character.goals,
            "emotions": character.emotions,
        }

    def _deserialize_webtoon(self, data: dict) -> Webtoon:
        """Deserialize dictionary to webtoon entity"""
        from datetime import datetime

        from app.domain.entities.character import Character, CharacterAppearance
        from app.domain.entities.panel import Panel, SpeechBubble
        from app.domain.entities.scene import Scene
        from app.domain.entities.webtoon import Webtoon
        from app.domain.value_objects.dimensions import PanelDimensions, PanelSize
        from app.domain.value_objects.position import Position
        from app.domain.value_objects.style import ArtStyle

        webtoon = Webtoon(
            id=UUID(data["id"]),
            title=data["title"],
            description=data["description"],
            art_style=ArtStyle(data["art_style"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            is_published=data["is_published"],
            metadata=data.get("metadata", {}),
        )

        for char_data in data.get("characters", []):
            appearance = CharacterAppearance(
                height=char_data["appearance"]["height"],
                build=char_data["appearance"]["build"],
                hair_color=char_data["appearance"]["hair_color"],
                hair_style=char_data["appearance"]["hair_style"],
                eye_color=char_data["appearance"]["eye_color"],
                skin_tone=char_data["appearance"]["skin_tone"],
                distinctive_features=char_data["appearance"]["distinctive_features"],
                clothing_style=char_data["appearance"]["clothing_style"],
            )

            character = Character(
                id=UUID(char_data["id"]),
                name=char_data["name"],
                description=char_data["description"],
                appearance=appearance,
                personality_traits=char_data["personality_traits"],
                role=char_data["role"],
                relationships=char_data.get("relationships", {}),
                backstory=char_data.get("backstory", ""),
                goals=char_data.get("goals", []),
                emotions=char_data.get("emotions", {}),
            )
            webtoon.characters.append(character)

        for panel_data in data.get("panels", []):
            scene_data = panel_data["scene"]
            scene = Scene(
                id=UUID(scene_data["id"]),
                description=scene_data["description"],
                setting=scene_data["setting"],
                time_of_day=scene_data["time_of_day"],
                weather=scene_data["weather"],
                mood=scene_data["mood"],
                character_names=scene_data["character_names"],
                character_positions=scene_data["character_positions"],
                character_expressions=scene_data["character_expressions"],
                actions=scene_data["actions"],
                camera_angle=scene_data["camera_angle"],
                lighting=scene_data["lighting"],
                composition_notes=scene_data["composition_notes"],
            )

            dim_data = panel_data["dimensions"]
            dimensions = PanelDimensions(
                size=PanelSize(dim_data["size"]),
                width=dim_data["width"],
                height=dim_data["height"],
                aspect_ratio=dim_data["aspect_ratio"],
            )

            panel = Panel(
                id=UUID(panel_data["id"]),
                sequence_number=panel_data["sequence_number"],
                scene=scene,
                dimensions=dimensions,
                visual_effects=panel_data["visual_effects"],
                image_url=panel_data["image_url"],
                generated_at=datetime.fromisoformat(panel_data["generated_at"])
                if panel_data["generated_at"]
                else None,
                metadata=panel_data.get("metadata", {}),
            )

            for bubble_data in panel_data["speech_bubbles"]:
                pos_data = bubble_data["position"]
                position = Position(
                    x_percent=pos_data["x_percent"],
                    y_percent=pos_data["y_percent"],
                    anchor=pos_data["anchor"],
                )

                bubble = SpeechBubble(
                    id=UUID(bubble_data["id"]),
                    character_name=bubble_data["character_name"],
                    text=bubble_data["text"],
                    position=position,
                    style=bubble_data["style"],
                    tail_direction=bubble_data["tail_direction"],
                )
                panel.speech_bubbles.append(bubble)

            webtoon.panels.append(panel)

        return webtoon

    async def create(self, entity: Webtoon) -> Webtoon:
        """Create a new webtoon entity"""
        try:
            key = self._get_key(entity.id)
            data = self._serialize_webtoon(entity)
            success = await self.storage.store_json(key, data)
            if not success:
                raise RuntimeError(f"Failed to create webtoon {entity.id}")
            logger.debug(f"Created webtoon: {entity.id}")
            return entity
        except Exception as e:
            logger.error(f"Error creating webtoon {entity.id}: {str(e)}")
            raise

    async def update(self, entity_id: UUID, entity: Webtoon) -> Optional[Webtoon]:
        """Update a webtoon entity"""
        try:
            if not await self.exists(entity_id):
                logger.warning(f"Webtoon {entity_id} not found for update")
                return None
            key = self._get_key(entity_id)
            data = self._serialize_webtoon(entity)
            success = await self.storage.store_json(key, data)
            if not success:
                raise RuntimeError(f"Failed to update webtoon {entity_id}")
            logger.debug(f"Updated webtoon: {entity_id}")
            return entity
        except Exception as e:
            logger.error(f"Error updating webtoon {entity_id}: {str(e)}")
            raise

    async def save(self, entity: Webtoon) -> Webtoon:
        """Save a webtoon entity"""
        try:
            key = self._get_key(entity.id)
            data = self._serialize_webtoon(entity)
            success = await self.storage.store_json(key, data)
            if not success:
                raise RuntimeError(f"Failed to save webtoon {entity.id}")
            logger.debug(f"Saved webtoon: {entity.id}")
            return entity
        except Exception as e:
            logger.error(f"Error saving webtoon {entity.id}: {str(e)}")
            raise

    async def get_by_id(self, entity_id: UUID) -> Optional[Webtoon]:
        """Get webtoon by ID"""
        try:
            key = self._get_key(entity_id)
            data = await self.storage.retrieve_json(key)
            if data is None:
                return None
            return self._deserialize_webtoon(data)
        except Exception as e:
            logger.error(f"Error retrieving webtoon {entity_id}: {str(e)}")
            return None

    async def get_all(self) -> List[Webtoon]:
        """Get all webtoons"""
        try:
            keys = await self.storage.list_keys(f"{self.key_prefix}*")
            webtoons = []
            for key in keys:
                data = await self.storage.retrieve_json(key)
                if data is not None:
                    webtoon = self._deserialize_webtoon(data)
                    webtoons.append(webtoon)
            return webtoons
        except Exception as e:
            logger.error(f"Error retrieving all webtoons: {str(e)}")
            return []

    async def delete(self, entity_id: UUID) -> bool:
        """Delete webtoon by ID"""
        try:
            key = self._get_key(entity_id)
            return await self.storage.delete(key)
        except Exception as e:
            logger.error(f"Error deleting webtoon {entity_id}: {str(e)}")
            return False

    async def exists(self, entity_id: UUID) -> bool:
        """Check if webtoon exists"""
        try:
            key = self._get_key(entity_id)
            return await self.storage.exists(key)
        except Exception as e:
            logger.error(f"Error checking webtoon existence {entity_id}: {str(e)}")
            return False

    async def get_by_title(self, title: str) -> Optional[Webtoon]:
        """Get webtoon by title"""
        webtoons = await self.get_all()
        return next((w for w in webtoons if w.title == title), None)

    async def get_published(self) -> List[Webtoon]:
        """Get all published webtoons"""
        webtoons = await self.get_all()
        return [w for w in webtoons if w.is_published]

    async def search_by_keyword(self, keyword: str) -> List[Webtoon]:
        """Search webtoons by keyword in title or description"""
        webtoons = await self.get_all()
        keyword_lower = keyword.lower()
        return [
            w
            for w in webtoons
            if keyword_lower in w.title.lower()
            or keyword_lower in w.description.lower()
        ]
