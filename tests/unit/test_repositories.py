"""
Unit tests for repositories - Extended
"""
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.domain.entities.character import Character, CharacterAppearance
from app.domain.entities.panel import Panel, SpeechBubble
from app.domain.entities.scene import Scene
from app.domain.entities.webtoon import Webtoon
from app.domain.value_objects.dimensions import PanelDimensions, PanelSize
from app.domain.value_objects.position import Position
from app.domain.value_objects.style import ArtStyle


class TestWebtoonRepositoryComplex:
    """Test complex WebtoonRepository operations"""

    @pytest.mark.asyncio
    async def test_save_complex_webtoon(self, webtoon_repository):
        """Test saving webtoon with characters and panels"""
        # Create complex webtoon
        webtoon = Webtoon(
            title="Complex Test Webtoon",
            description="A webtoon with characters and panels",
            art_style=ArtStyle.MANGA,
        )

        # Add character
        appearance = CharacterAppearance(
            height="tall", hair_color="black", eye_color="blue"
        )
        character = Character(
            name="Hero",
            description="Main character",
            appearance=appearance,
            personality_traits=["brave", "kind"],
            role="protagonist",
        )
        webtoon.add_character(character)

        # Add panel with scene and speech bubble
        scene = Scene(
            description="Hero standing in city",
            setting="Urban environment",
            character_names=["Hero"],
            mood="determined",
        )

        panel = Panel(scene=scene, dimensions=PanelDimensions.from_size(PanelSize.FULL))

        # Add speech bubble
        position = Position(x_percent=30, y_percent=20)
        bubble = SpeechBubble(
            character_name="Hero",
            text="I will save the city!",
            position=position,
            style="normal",
        )
        panel.add_speech_bubble(bubble)
        panel.image_url = "http://example.com/image.png"
        panel.generated_at = datetime.now(UTC)

        webtoon.add_panel(panel)

        # Save and retrieve
        saved_webtoon = await webtoon_repository.save(webtoon)
        retrieved_webtoon = await webtoon_repository.get_by_id(webtoon.id)

        # Verify complex structure
        assert retrieved_webtoon is not None
        assert retrieved_webtoon.title == "Complex Test Webtoon"
        assert len(retrieved_webtoon.characters) == 1
        assert len(retrieved_webtoon.panels) == 1

        # Verify character
        saved_character = retrieved_webtoon.characters[0]
        assert saved_character.name == "Hero"
        assert saved_character.appearance.height == "tall"
        assert "brave" in saved_character.personality_traits

        # Verify panel
        saved_panel = retrieved_webtoon.panels[0]
        assert saved_panel.scene.description == "Hero standing in city"
        assert saved_panel.scene.mood == "determined"
        assert len(saved_panel.speech_bubbles) == 1

        # Verify speech bubble
        saved_bubble = saved_panel.speech_bubbles[0]
        assert saved_bubble.character_name == "Hero"
        assert saved_bubble.text == "I will save the city!"
        assert saved_bubble.position.x_percent == 30


class TestWebtoonRepository:
    """Test WebtoonRepository"""

    @pytest.mark.asyncio
    async def test_save_and_retrieve_webtoon(self, webtoon_repository):
        """Test saving and retrieving webtoon"""
        webtoon = Webtoon(
            title="Test Webtoon",
            description="Test description",
            art_style=ArtStyle.MANGA,
        )

        # Save webtoon
        saved_webtoon = await webtoon_repository.save(webtoon)
        assert saved_webtoon.id == webtoon.id

        # Retrieve webtoon
        retrieved_webtoon = await webtoon_repository.get_by_id(webtoon.id)
        assert retrieved_webtoon is not None
        assert retrieved_webtoon.title == "Test Webtoon"
        assert retrieved_webtoon.art_style == ArtStyle.MANGA

    @pytest.mark.asyncio
    async def test_get_nonexistent_webtoon(self, webtoon_repository):
        """Test retrieving non-existent webtoon"""
        result = await webtoon_repository.get_by_id(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_search_by_keyword(self, webtoon_repository):
        """Test searching webtoons by keyword"""
        webtoon1 = Webtoon(title="Dragon Adventure", description="Epic fantasy")
        webtoon2 = Webtoon(title="Space Opera", description="Sci-fi adventure")

        await webtoon_repository.save(webtoon1)
        await webtoon_repository.save(webtoon2)

        # Search by title
        results = await webtoon_repository.search_by_keyword("Dragon")
        assert len(results) == 1
        assert results[0].title == "Dragon Adventure"

        # Search by description
        results = await webtoon_repository.search_by_keyword("adventure")
        assert len(results) == 2


class TestTaskRepository:
    """Test TaskRepository"""

    @pytest.mark.asyncio
    async def test_save_and_retrieve_task(self, task_repository):
        """Test saving and retrieving task"""
        task = GenerationTask(
            task_type=TaskType.WEBTOON_GENERATION, input_data={"prompt": "test prompt"}
        )

        # Save task
        saved_task = await task_repository.save(task)
        assert saved_task.id == task.id

        # Retrieve task
        retrieved_task = await task_repository.get_by_id(task.id)
        assert retrieved_task is not None
        assert retrieved_task.task_type == TaskType.WEBTOON_GENERATION
        assert retrieved_task.input_data["prompt"] == "test prompt"

    @pytest.mark.asyncio
    async def test_get_by_status(self, task_repository):
        """Test getting tasks by status"""
        task1 = GenerationTask(task_type=TaskType.WEBTOON_GENERATION)
        task2 = GenerationTask(task_type=TaskType.PANEL_GENERATION)

        task1.start()  # Set to processing
        # task2 remains pending

        await task_repository.save(task1)
        await task_repository.save(task2)

        # Get pending tasks
        pending_tasks = await task_repository.get_by_status(TaskStatus.PENDING)
        assert len(pending_tasks) == 1
        assert pending_tasks[0].id == task2.id

        # Get processing tasks
        processing_tasks = await task_repository.get_by_status(TaskStatus.PROCESSING)
        assert len(processing_tasks) == 1
        assert processing_tasks[0].id == task1.id
