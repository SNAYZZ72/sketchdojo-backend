# =============================================================================
# tests/performance/test_api_performance.py
# =============================================================================
import asyncio
import time

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_api_response_times(client: AsyncClient, auth_headers):
    """Test API response times for key endpoints."""

    # Test authentication endpoint
    start_time = time.time()
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    auth_time = time.time() - start_time

    assert response.status_code in [200, 401]
    assert auth_time < 1.0  # Should respond within 1 second

    # Test project listing
    start_time = time.time()
    response = await client.get("/api/v1/projects", headers=auth_headers)
    projects_time = time.time() - start_time

    assert response.status_code in [200, 401]
    assert projects_time < 2.0  # Should respond within 2 seconds

    # Test health check
    start_time = time.time()
    response = await client.get("/health")
    health_time = time.time() - start_time

    assert response.status_code == 200
    assert health_time < 0.5  # Health check should be very fast


@pytest.mark.asyncio
async def test_concurrent_requests(client: AsyncClient, auth_headers):
    """Test handling of concurrent requests."""

    async def make_request():
        return await client.get("/api/v1/projects", headers=auth_headers)

    # Make 10 concurrent requests
    start_time = time.time()
    tasks = [make_request() for _ in range(10)]
    responses = await asyncio.gather(*tasks)
    total_time = time.time() - start_time

    # All requests should complete
    assert len(responses) == 10

    # Should handle concurrent requests efficiently
    assert total_time < 5.0  # All 10 requests within 5 seconds

    # Check response codes
    for response in responses:
        assert response.status_code in [200, 401]


@pytest.mark.asyncio
async def test_large_payload_handling(client: AsyncClient, auth_headers):
    """Test handling of large request payloads."""

    # Create a large character description
    large_description = "A" * 5000  # 5KB description

    large_character_data = {
        "name": "Large Character",
        "role": "protagonist",
        "description": large_description,
        "appearance": {
            "age_range": "adult",
            "gender": "female",
            "height": "average",
            "build": "average",
            "hair_color": "brown",
            "hair_style": "long",
            "eye_color": "green",
            "skin_tone": "fair",
            "distinctive_features": ["tattoo"] * 100,  # Large list
        },
        "personality": {
            "traits": ["brave"] * 50,  # Large list
            "motivations": ["save world"] * 20,
            "fears": ["spiders"] * 30,
            "speech_style": "formal",
        },
    }

    # First create a project
    project_response = await client.post(
        "/api/v1/projects",
        headers=auth_headers,
        json={"title": "Large Data Test", "description": "Testing large payloads"},
    )

    if project_response.status_code == 201:
        project_id = project_response.json()["id"]

        # Test large character creation
        start_time = time.time()
        response = await client.post(
            "/api/v1/characters",
            headers=auth_headers,
            params={"project_id": project_id},
            json=large_character_data,
        )
        creation_time = time.time() - start_time

        # Should handle large payloads gracefully
        assert response.status_code in [201, 400, 413]  # Created, bad request, or payload too large
        assert creation_time < 10.0  # Should not take too long
