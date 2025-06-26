"""
Unit tests for webtoon key generation utilities.
"""
import pytest
from uuid import UUID, uuid4

from app.infrastructure.utils.webtoon_keys import (
    webtoon_key,
    webtoon_list_key,
    webtoon_search_index_key,
    webtoon_user_webtoons_key,
    webtoon_status_key,
    webtoon_episodes_key,
    webtoon_pattern,
    webtoon_episodes_pattern,
    webtoon_episode_key,
)

# Test data
TEST_WEBTOON_ID = "123e4567-e89b-12d3-a456-426614174000"
TEST_USER_ID = "123e4567-e89b-12d3-a456-426614174001"
TEST_EPISODE_NUMBER = 1

class TestWebtoonKeys:
    """Test cases for webtoon key generation utilities."""

    def test_webtoon_key_with_string_id(self):
        """Test generating a webtoon key with a string ID."""
        assert webtoon_key(TEST_WEBTOON_ID) == f"webtoon:{TEST_WEBTOON_ID}"

    def test_webtoon_key_with_uuid(self):
        """Test generating a webtoon key with a UUID object."""
        webtoon_uuid = UUID(TEST_WEBTOON_ID)
        assert webtoon_key(webtoon_uuid) == f"webtoon:{TEST_WEBTOON_ID}"

    def test_webtoon_list_key(self):
        """Test generating the webtoon list key."""
        assert webtoon_list_key() == "webtoons:all"

    def test_webtoon_search_index_key(self):
        """Test generating the webtoon search index key."""
        assert webtoon_search_index_key() == "webtoon:search:index"

    def test_webtoon_user_webtoons_key_with_string_id(self):
        """Test generating a user's webtoons key with a string ID."""
        assert webtoon_user_webtoons_key(TEST_USER_ID) == f"user:{TEST_USER_ID}:webtoons"

    def test_webtoon_user_webtoons_key_with_uuid(self):
        """Test generating a user's webtoons key with a UUID object."""
        user_uuid = UUID(TEST_USER_ID)
        assert webtoon_user_webtoons_key(user_uuid) == f"user:{TEST_USER_ID}:webtoons"

    def test_webtoon_status_key_with_string_id(self):
        """Test generating a webtoon status key with a string ID."""
        assert webtoon_status_key(TEST_WEBTOON_ID) == f"webtoon:{TEST_WEBTOON_ID}:status"

    def test_webtoon_episodes_key_with_string_id(self):
        """Test generating a webtoon episodes key with a string ID."""
        assert webtoon_episodes_key(TEST_WEBTOON_ID) == f"webtoon:{TEST_WEBTOON_ID}:episodes"

    def test_webtoon_episodes_key_with_uuid(self):
        """Test generating a webtoon episodes key with a UUID object."""
        webtoon_uuid = UUID(TEST_WEBTOON_ID)
        assert webtoon_episodes_key(webtoon_uuid) == f"webtoon:{TEST_WEBTOON_ID}:episodes"

    def test_webtoon_pattern(self):
        """Test generating the webtoon pattern."""
        assert webtoon_pattern() == "webtoon:*"

    def test_webtoon_episodes_pattern(self):
        """Test generating the webtoon episodes pattern."""
        assert webtoon_episodes_pattern() == "webtoon:*:episodes"

    def test_webtoon_episode_key_with_string_id(self):
        """Test generating a webtoon episode key with a string ID."""
        assert webtoon_episode_key(TEST_WEBTOON_ID, TEST_EPISODE_NUMBER) == \
               f"webtoon:{TEST_WEBTOON_ID}:episode:{TEST_EPISODE_NUMBER}"

    def test_webtoon_episode_key_with_uuid(self):
        """Test generating a webtoon episode key with a UUID object."""
        webtoon_uuid = UUID(TEST_WEBTOON_ID)
        assert webtoon_episode_key(webtoon_uuid, TEST_EPISODE_NUMBER) == \
               f"webtoon:{TEST_WEBTOON_ID}:episode:{TEST_EPISODE_NUMBER}"
