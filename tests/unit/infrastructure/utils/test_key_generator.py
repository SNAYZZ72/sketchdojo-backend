"""
Tests for the KeyGenerator utility.
"""
import pytest
from uuid import UUID, uuid4

from app.infrastructure.utils.key_generator import KeyGenerator, chat_keys


def test_generate_key_basic():
    """Test basic key generation."""
    assert KeyGenerator.generate_key("test") == "test"
    assert KeyGenerator.generate_key("test", "key") == "test:key"
    assert KeyGenerator.generate_key("test", "key", "subkey") == "test:key:subkey"


def test_generate_key_with_different_types():
    """Test key generation with different types."""
    assert KeyGenerator.generate_key("test", 123) == "test:123"
    assert KeyGenerator.generate_key("test", 3.14) == "test:3.14"
    assert KeyGenerator.generate_key("test", True) == "test:True"
    assert KeyGenerator.generate_key("test", "key", 123) == "test:key:123"


def test_generate_key_with_none():
    """Test key generation with None values."""
    assert KeyGenerator.generate_key("test", None) == "test"
    assert KeyGenerator.generate_key("test", "key", None, "subkey") == "test:key:subkey"
    assert KeyGenerator.generate_key("test", "", "key") == "test::key"


def test_generate_key_with_uuid():
    """Test key generation with UUIDs."""
    test_uuid = uuid4()
    expected = f"test:{str(test_uuid)}"
    assert KeyGenerator.generate_key("test", test_uuid) == expected


def test_generate_pattern():
    """Test pattern generation."""
    assert KeyGenerator.generate_pattern("test") == "test*"
    assert KeyGenerator.generate_pattern("test", "key") == "test:key*"
    assert KeyGenerator.generate_pattern("test", "*") == "test:*"
    assert KeyGenerator.generate_pattern("test", "key", "*") == "test:key:*"


def test_namespace_key_generator():
    """Test the namespace key generator."""
    ns = KeyGenerator.for_namespace("test")
    assert str(ns) == "<NamespaceKeyGenerator: test>"
    assert ns.key("item", 123) == "test:item:123"
    assert ns.pattern("item", "*") == "test:item:*"


def test_chat_keys():
    """Test the chat keys generator."""
    test_uuid = uuid4()
    
    # Test message key
    assert chat_keys.message(test_uuid) == f"chat:message:{test_uuid}"
    assert chat_keys.message(str(test_uuid)) == f"chat:message:{test_uuid}"
    
    # Test room key
    assert chat_keys.room(test_uuid) == f"chat:room:{test_uuid}"
    
    # Test webtoon messages key
    assert chat_keys.webtoon_messages(test_uuid) == f"chat:webtoon:{test_uuid}:messages"
    
    # Test user messages key
    assert chat_keys.user_messages(test_uuid) == f"chat:user:{test_uuid}:messages"


def test_custom_separator():
    """Test key generation with custom separator."""
    ns = KeyGenerator.for_namespace("test", separator="_")
    assert ns.key("item", 123) == "test_item_123"
    assert ns.pattern("item", "*") == "test_item_*"
    
    # Test with custom separator in generate_key
    assert KeyGenerator.generate_key("test", "key", separator="_") == "test_key"
    assert KeyGenerator.generate_pattern("test", "key", separator="_") == "test_key*"


def test_chat_keys_with_custom_separator():
    """Test chat keys with custom separator."""
    custom_chat_keys = KeyGenerator.for_namespace("chat", separator="_")
    test_uuid = uuid4()
    
    # Test with custom separator
    assert custom_chat_keys.key("message", test_uuid) == f"chat_message_{test_uuid}"
    assert custom_chat_keys.pattern("message", "*") == "chat_message_*"


def test_edge_cases():
    """Test edge cases in key generation."""
    # Empty parts
    assert KeyGenerator.generate_key("") == ""
    assert KeyGenerator.generate_key("", "") == ":"
    
    # Special characters
    assert KeyGenerator.generate_key("test", "key/with/slashes") == "test:key/with/slashes"
    assert KeyGenerator.generate_key("test", "key:with:colons") == "test:key:with:colons"
    
    # Very long strings
    long_str = "x" * 1000
    assert KeyGenerator.generate_key("test", long_str) == f"test:{long_str}"
