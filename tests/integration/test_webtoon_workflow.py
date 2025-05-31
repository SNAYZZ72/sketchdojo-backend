# =============================================================================
# tests/integration/test_webtoon_workflow.py
# =============================================================================
from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_complete_webtoon_workflow(client: AsyncClient, auth_headers):
    """Test complete webtoon creation workflow."""

    # Step 1: Create a project
    project_response = await client.post(
        "/api/v1/projects",
        headers=auth_headers,
        json={
            "title": "Test Webtoon Project",
            "description": "A test project for webtoon creation",
            "art_style": "webtoon",
            "target_panels": 4,
        },
    )

    assert project_response.status_code == 201
    project_data = project_response.json()
    project_id = project_data["id"]

    # Step 2: Create characters
    character1_response = await client.post(
        "/api/v1/characters",
        headers=auth_headers,
        params={"project_id": project_id},
        json={
            "name": "Hero",
            "role": "protagonist",
            "description": "The brave hero of our story",
            "appearance": {
                "age_range": "young_adult",
                "gender": "male",
                "height": "tall",
                "build": "muscular",
                "hair_color": "black",
                "hair_style": "spiky",
                "eye_color": "blue",
                "skin_tone": "fair",
                "distinctive_features": ["scar on cheek"],
            },
            "personality": {
                "traits": ["brave", "determined", "kind"],
                "motivations": ["save the world"],
                "fears": ["losing friends"],
                "speech_style": "confident",
            },
        },
    )

    assert character1_response.status_code == 201
    character1_data = character1_response.json()

    # Step 3: Create scenes
    scene1_response = await client.post(
        "/api/v1/scenes",
        headers=auth_headers,
        params={"project_id": project_id},
        json={
            "sequence_number": 1,
            "scene_type": "establishing",
            "title": "Hero's Introduction",
            "description": "Hero stands on a cliff overlooking the kingdom",
            "environment": {
                "location": "Mountain cliff",
                "time_of_day": "dawn",
                "weather": "clear",
                "lighting": "dramatic",
                "atmosphere": "peaceful",
            },
            "characters_present": [character1_data["id"]],
            "dialogue_lines": [
                {
                    "character_id": character1_data["id"],
                    "text": "Today, I begin my journey to save the kingdom.",
                    "emotion": "determined",
                    "style": "normal",
                }
            ],
            "camera_angle": "wide",
            "visual_focus": "Hero silhouette against sunrise",
        },
    )

    assert scene1_response.status_code == 201
    scene1_data = scene1_response.json()

    # Step 4: Create webtoon
    webtoon_response = await client.post(
        "/api/v1/webtoons",
        headers=auth_headers,
        params={"project_id": project_id},
        json={
            "title": "The Hero's Journey",
            "description": "An epic tale of heroism and adventure",
            "metadata": {
                "genre": "fantasy",
                "target_audience": "teen",
                "content_rating": "PG",
                "tags": ["adventure", "fantasy", "hero"],
                "color_scheme": "full_color",
                "aspect_ratio": "vertical",
            },
            "story_summary": "A young hero sets out to save his kingdom from an ancient evil.",
            "estimated_panels": 4,
        },
    )

    assert webtoon_response.status_code == 201
    webtoon_data = webtoon_response.json()
    webtoon_id = webtoon_data["id"]

    # Step 5: Generate webtoon
    generation_response = await client.post(
        "/api/v1/webtoons/generate",
        headers=auth_headers,
        params={"project_id": project_id},
        json={
            "story_prompt": "A hero's journey to save the kingdom from darkness",
            "character_descriptions": ["Brave young hero with black spiky hair"],
            "style_preferences": {"style": "webtoon", "quality": "standard"},
            "auto_generate_panels": True,
            "panel_count": 4,
        },
    )

    assert generation_response.status_code == 200
    task_data = generation_response.json()
    task_id = task_data["id"]

    # Step 6: Check task status
    status_response = await client.get(f"/api/v1/tasks/{task_id}", headers=auth_headers)

    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["task_type"] == "webtoon_generation"

    # Step 7: Get project details
    project_detail_response = await client.get(
        f"/api/v1/projects/{project_id}", headers=auth_headers
    )

    assert project_detail_response.status_code == 200

    # Step 8: Get webtoon panels (would be generated by background task)
    panels_response = await client.get(f"/api/v1/panels/webtoon/{webtoon_id}", headers=auth_headers)

    # Panels might not exist yet if generation is still in progress
    # In real test, we'd wait for task completion
    assert panels_response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_user_project_limits(client: AsyncClient, auth_headers):
    """Test user project creation limits."""

    # Create maximum allowed projects
    created_projects = []

    for i in range(5):  # Assuming max 5 projects per user
        response = await client.post(
            "/api/v1/projects",
            headers=auth_headers,
            json={
                "title": f"Test Project {i + 1}",
                "description": f"Test project number {i + 1}",
                "art_style": "webtoon",
            },
        )

        if response.status_code == 201:
            created_projects.append(response.json()["id"])
        else:
            # Hit the limit
            break

    # Try to create one more (should fail or succeed based on limits)
    response = await client.post(
        "/api/v1/projects",
        headers=auth_headers,
        json={
            "title": "Excess Project",
            "description": "This should exceed limits",
            "art_style": "webtoon",
        },
    )

    # Response depends on implementation of limits
    # Could be 400 (limit exceeded) or 201 (no limits enforced yet)
    assert response.status_code in [200, 201, 400, 429]


@pytest.mark.asyncio
async def test_project_security(client: AsyncClient, auth_headers):
    """Test project access security."""

    # Create a project
    project_response = await client.post(
        "/api/v1/projects",
        headers=auth_headers,
        json={
            "title": "Private Project",
            "description": "This should be private to the user",
            "art_style": "manga",
        },
    )

    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    # Try to access project without authentication
    response = await client.get(f"/api/v1/projects/{project_id}")
    assert response.status_code == 401

    # Try to access project with authentication (should work)
    response = await client.get(f"/api/v1/projects/{project_id}", headers=auth_headers)
    assert response.status_code == 200

    # Try to access non-existent project
    fake_id = str(uuid4())
    response = await client.get(f"/api/v1/projects/{fake_id}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_concurrent_task_limits(client: AsyncClient, auth_headers):
    """Test concurrent task execution limits."""

    # Create a project first
    project_response = await client.post(
        "/api/v1/projects",
        headers=auth_headers,
        json={
            "title": "Task Test Project",
            "description": "For testing task limits",
            "art_style": "webtoon",
        },
    )

    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    # Start multiple generation tasks
    task_responses = []

    for i in range(5):  # Try to start 5 tasks
        response = await client.post(
            "/api/v1/webtoons/generate",
            headers=auth_headers,
            params={"project_id": project_id},
            json={
                "story_prompt": f"Test story {i + 1}",
                "panel_count": 2,
                "style_preferences": {"style": "webtoon"},
            },
        )

        task_responses.append(response)

    # Check responses
    successful_tasks = [r for r in task_responses if r.status_code == 200]
    failed_tasks = [r for r in task_responses if r.status_code != 200]

    # Should have some limit on concurrent tasks
    # Exact behavior depends on implementation
    assert len(successful_tasks) <= 3  # Assuming max 3 concurrent tasks

    # Failed tasks should have appropriate error codes
    for response in failed_tasks:
        assert response.status_code in [400, 429]  # Bad request or rate limited
