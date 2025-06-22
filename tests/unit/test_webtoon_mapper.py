# tests/unit/test_webtoon_mapper.py
"""
Tests for WebtoonDataMapper
"""
import uuid
from datetime import datetime

import pytest
from uuid import UUID

from app.domain.entities.webtoon import Webtoon
from app.domain.entities.character import Character
from app.domain.entities.panel import Panel
from app.domain.mappers.webtoon_mapper import WebtoonDataMapper


class TestWebtoonDataMapper:
    """Test WebtoonDataMapper functionality"""

    def setup_method(self):
        """Initialize test data and mapper"""
        self.mapper = WebtoonDataMapper()
        self.webtoon_id = uuid.uuid4()
        self.character_id = uuid.uuid4()
        self.panel_id = uuid.uuid4()
        
        # Create a sample webtoon
        character = Character(
            id=self.character_id,
            name="Test Character",
            description="A test character",
            personality_traits=["brave", "smart"],
            backstory="A long time ago..."
        )
        
        from app.domain.entities.scene import Scene
        from app.domain.value_objects.dimensions import PanelDimensions
        from app.domain.entities.panel import SpeechBubble
        
        # Create a speech bubble
        speech_bubble = SpeechBubble(
            character_name="Test Character",
            text="Hello world!"
        )
        
        panel = Panel(
            id=self.panel_id,
            sequence_number=1,
            scene=Scene(character_names=[character.name]),
            image_url="http://example.com/panel.jpg",
            speech_bubbles=[speech_bubble],
            dimensions=PanelDimensions()
        )
        
        self.webtoon = Webtoon(
            id=self.webtoon_id,
            title="Test Webtoon",
            description="A test webtoon",
            art_style="webtoon",
            panels=[panel],
            characters=[character],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_published=False,
            metadata={"tags": ["test", "sample"]},
        )

    def test_to_dict(self):
        """Test conversion of Webtoon to dict"""
        # Convert to dict
        webtoon_dict = self.mapper.to_dict(self.webtoon)
        
        # Validate top-level properties
        assert webtoon_dict["id"] == str(self.webtoon_id)
        assert webtoon_dict["title"] == "Test Webtoon"
        assert webtoon_dict["description"] == "A test webtoon"
        assert webtoon_dict["art_style"] == "webtoon"
        assert webtoon_dict["is_published"] is False
        assert "tags" in webtoon_dict["metadata"]
        assert "test" in webtoon_dict["metadata"]["tags"]
        assert "sample" in webtoon_dict["metadata"]["tags"]
        
        # Validate panels
        assert len(webtoon_dict["panels"]) == 1
        panel_dict = webtoon_dict["panels"][0]
        assert panel_dict["id"] == str(self.panel_id)
        assert panel_dict["sequence_number"] == 1
        
        # Validate characters
        assert len(webtoon_dict["characters"]) == 1
        character_dict = webtoon_dict["characters"][0]
        assert character_dict["id"] == str(self.character_id)
        assert character_dict["name"] == "Test Character"

    def test_from_dict(self):
        """Test conversion from dict to Webtoon"""
        # First convert to dict
        webtoon_dict = self.mapper.to_dict(self.webtoon)
        
        # Then convert back to object
        webtoon = self.mapper.from_dict(webtoon_dict)
        
        # Validate object
        assert isinstance(webtoon, Webtoon)
        assert webtoon.id == self.webtoon_id
        assert webtoon.title == "Test Webtoon"
        assert webtoon.description == "A test webtoon"
        assert webtoon.art_style == "webtoon"
        assert webtoon.is_published is False
        assert "tags" in webtoon.metadata
        assert "test" in webtoon.metadata["tags"]
        assert "sample" in webtoon.metadata["tags"]
        
        # Validate panels
        assert len(webtoon.panels) == 1
        panel = webtoon.panels[0]
        assert isinstance(panel, Panel)
        assert panel.id == self.panel_id
        assert panel.sequence_number == 1
        
        # Validate characters
        assert len(webtoon.characters) == 1
        character = webtoon.characters[0]
        assert isinstance(character, Character)
        assert character.id == self.character_id
        assert character.name == "Test Character"
        
    def test_round_trip_conversion(self):
        """Test that converting to dict and back preserves all properties"""
        # Convert to dict and back
        webtoon_dict = self.mapper.to_dict(self.webtoon)
        webtoon_new = self.mapper.from_dict(webtoon_dict)
        
        # Test equality of key properties
        assert webtoon_new.id == self.webtoon.id
        assert webtoon_new.title == self.webtoon.title
        assert webtoon_new.description == self.webtoon.description
        assert webtoon_new.art_style == self.webtoon.art_style
        assert webtoon_new.is_published == self.webtoon.is_published
        
        # Test nested objects
        assert len(webtoon_new.panels) == len(self.webtoon.panels)
        assert len(webtoon_new.characters) == len(self.webtoon.characters)
        
        # Test panel details
        assert webtoon_new.panels[0].sequence_number == self.webtoon.panels[0].sequence_number
        
        # Test character details
        assert webtoon_new.characters[0].name == self.webtoon.characters[0].name
