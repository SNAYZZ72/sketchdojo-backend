"""
Key generation utilities for Redis storage.
"""
from typing import Optional, Union
from uuid import UUID


class KeyGenerator:
    """
    Utility class for generating consistent Redis keys.
    """
    
    @staticmethod
    def generate_key(
        prefix: str, 
        *parts: Union[str, UUID, int, float, bool],
        separator: str = ":"
    ) -> str:
        """
        Generate a Redis key from parts.
        
        Args:
            prefix: The key prefix (e.g., 'chat', 'user')
            *parts: Additional parts to include in the key
            separator: Separator between key parts (default: ':')
            
        Returns:
            str: Generated Redis key
            
        Examples:
            >>> KeyGenerator.generate_key("chat", "message", "123")
            'chat:message:123'
            >>> KeyGenerator.generate_key("user", 123, "profile")
            'user:123:profile'
        """
        key_parts = [str(prefix)]
        for part in parts:
            if part is not None:
                key_parts.append(str(part))
        return separator.join(key_parts)
    
    @staticmethod
    def generate_pattern(
        prefix: str, 
        *parts: Union[str, int, None],
        separator: str = ":"
    ) -> str:
        """
        Generate a Redis key pattern for scanning.
        
        Args:
            prefix: The key prefix (e.g., 'chat', 'user')
            *parts: Additional parts to include in the pattern (use '*' for wildcards)
            separator: Separator between key parts (default= ':')
            
        Returns:
            str: Generated Redis key pattern with a single trailing '*' if no wildcard is present
            
        Examples:
            >>> KeyGenerator.generate_pattern("test")
            'test*'
            >>> KeyGenerator.generate_pattern("test", "key")
            'test:key*'
            >>> KeyGenerator.generate_pattern("test", "*")
            'test:*'
            >>> KeyGenerator.generate_pattern("test", "key", "*")
            'test:key:*'
        """
        # If no parts are provided, add a wildcard
        if not parts:
            return f"{prefix}*"
            
        # Check if the last part is a wildcard
        last_part = str(parts[-1])
        if last_part == "*":
            # If the last part is already a wildcard, don't add another one
            return (
                KeyGenerator.generate_key(prefix, *parts[:-1], separator=separator) +
                f"{separator}*"
            )
        else:
            # Otherwise, add a wildcard at the end
            return KeyGenerator.generate_key(prefix, *parts, separator=separator) + "*"
    
    @classmethod
    def for_namespace(cls, namespace: str, separator: str = ":") -> 'NamespaceKeyGenerator':
        """
        Create a key generator for a specific namespace.
        
        Args:
            namespace: The namespace for the key generator
            separator: Separator between key parts (default: ':')
            
        Returns:
            NamespaceKeyGenerator: A key generator instance for the namespace
        """
        return NamespaceKeyGenerator(namespace, separator)


class NamespaceKeyGenerator:
    """
    Key generator for a specific namespace.
    """
    
    def __init__(self, namespace: str, separator: str = ":"):
        """
        Initialize with a namespace.
        
        Args:
            namespace: The namespace for all keys
            separator: Separator between key parts (default: ':')
        """
        self.namespace = namespace
        self.separator = separator
    
    def key(self, *parts: Union[str, UUID, int, float, bool]) -> str:
        """
        Generate a key within the namespace.
        
        Args:
            *parts: Additional parts to include in the key
            
        Returns:
            str: Generated Redis key
        """
        return KeyGenerator.generate_key(self.namespace, *parts, separator=self.separator)
    
    def pattern(self, *parts: Union[str, int, None]) -> str:
        """
        Generate a key pattern within the namespace.
        
        Args:
            *parts: Additional parts to include in the pattern (use '*' for wildcards)
            
        Returns:
            str: Generated Redis key pattern
        """
        return KeyGenerator.generate_pattern(self.namespace, *parts, separator=self.separator)
    
    def __str__(self) -> str:
        return f"<NamespaceKeyGenerator: {self.namespace}>"


# Common key generators for easy access
class ChatKeys(NamespaceKeyGenerator):
    """Key generator for chat-related keys"""
    def __init__(self):
        super().__init__("chat")
    
    def message(self, message_id: Union[str, UUID]) -> str:
        """Key for a specific chat message"""
        return self.key("message", str(message_id))
    
    def room(self, room_id: Union[str, UUID]) -> str:
        """Key for a specific chat room"""
        return self.key("room", str(room_id))
    
    def webtoon_messages(self, webtoon_id: Union[str, UUID]) -> str:
        """Key for the sorted set of message IDs for a webtoon"""
        return self.key("webtoon", str(webtoon_id), "messages")
    
    def user_messages(self, user_id: Union[str, UUID]) -> str:
        """Key for the set of message IDs for a user"""
        return self.key("user", str(user_id), "messages")


# Global instances for common use
chat_keys = ChatKeys()
