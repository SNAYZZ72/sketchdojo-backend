"""
Unit tests for domain entities
"""

import pytest

from app.domain.entities.character import Character, CharacterAppearance
from app.domain.entities.generation_task import GenerationTask, TaskStatus, TaskType
from app.domain.entities.panel import Panel, SpeechBubble
from app.domain.entities.scene import Scene
from app.domain.entities.webtoon import Webtoon
from app.domain.value_objects.position import Position
from app.domain.value_objects.style import ArtStyle


class TestWebtoon:
    """Test Webtoon entity"""

    def test_create_webtoon(self):
        """Test webtoon creation"""
        webtoon = Webtoon(
            title="Test Webtoon",
            description="Test description",
            art_style=ArtStyle.WEBTOON,
        )

        assert webtoon.title == "Test Webtoon"
        assert webtoon.description == "Test description"
        assert webtoon.art_style == ArtStyle.WEBTOON
        assert webtoon.panel_count == 0
        assert webtoon.character_count == 0
        assert not webtoon.is_published

    def test_add_panel(self):
        """Test adding panel to webtoon"""
        webtoon = Webtoon(title="Test")
        panel = Panel()

        webtoon.add_panel(panel)

        assert webtoon.panel_count == 1
        assert panel.sequence_number == 0
        assert webtoon.get_panel_by_id(panel.id) == panel

    def test_add_character(self):
        """Test adding character to webtoon"""
        webtoon = Webtoon(title="Test")
        character = Character(name="Test Hero")

        webtoon.add_character(character)

        assert webtoon.character_count == 1
        assert webtoon.get_character_by_name("Test Hero") == character


class TestCharacter:
    """Test Character entity"""

    def test_create_character(self):
        """Test character creation"""
        appearance = CharacterAppearance(
            height="tall", hair_color="black", eye_color="blue"
        )

        character = Character(
            name="Test Hero",
            description="Brave protagonist",
            appearance=appearance,
            personality_traits=["brave", "kind"],
            role="protagonist",
        )

        assert character.name == "Test Hero"
        assert character.description == "Brave protagonist"
        assert character.role == "protagonist"
        assert "brave" in character.personality_traits

    def test_character_requires_name(self):
        """Test that character requires a name"""
        with pytest.raises(ValueError):
            Character(name="")


class TestPanel:
    """Test Panel entity"""

    def test_create_panel(self):
        """Test panel creation"""
        scene = Scene(description="Test scene")
        panel = Panel(scene=scene)

        assert panel.scene == scene
        assert panel.sequence_number == 0
        assert not panel.has_dialogue

    def test_add_speech_bubble(self):
        """Test adding speech bubble"""
        panel = Panel()
        position = Position(x_percent=50, y_percent=30)
        bubble = SpeechBubble(character_name="Hero", text="Hello!", position=position)

        panel.add_speech_bubble(bubble)

        assert panel.has_dialogue
        assert len(panel.speech_bubbles) == 1
        assert "Hero" in panel.get_characters_in_panel()


class TestGenerationTask:
    """Test GenerationTask entity"""

    def test_create_task(self):
        """Test task creation"""
        task = GenerationTask(
            task_type=TaskType.WEBTOON_GENERATION,
            input_data={"prompt": "test"},
        )

        assert task.status == TaskStatus.PENDING
        assert task.task_type == TaskType.WEBTOON_GENERATION
        assert not task.is_terminal

    def test_task_lifecycle(self):
        """Test task status transitions"""
        task = GenerationTask(task_type=TaskType.WEBTOON_GENERATION)

        # Start task
        task.start()
        assert task.status == TaskStatus.PROCESSING
        assert task.started_at is not None

        # Complete task
        result = {"webtoon_id": "123"}
        task.complete(result)
        assert task.status == TaskStatus.COMPLETED
        assert task.result == result
        assert task.is_terminal

    def test_task_failure(self):
        """Test task failure"""
        task = GenerationTask(task_type=TaskType.WEBTOON_GENERATION)

        task.fail("Test error")
        assert task.status == TaskStatus.FAILED
        assert task.error_message == "Test error"
        assert task.is_terminal
