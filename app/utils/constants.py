# =============================================================================
# app/utils/constants.py
# =============================================================================
"""
Application constants
"""

# File size limits (in bytes)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB

# Allowed file types
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"}

ALLOWED_DOCUMENT_TYPES = {"application/pdf", "text/plain", "application/json"}

# AI Generation limits
MAX_STORY_LENGTH = 10000  # characters
MAX_PANEL_DESCRIPTION_LENGTH = 2000  # characters
MAX_DIALOGUE_LENGTH = 500  # characters per bubble

# Cache TTL values (in seconds)
CACHE_TTL_SHORT = 300  # 5 minutes
CACHE_TTL_MEDIUM = 1800  # 30 minutes
CACHE_TTL_LONG = 3600  # 1 hour
CACHE_TTL_VERY_LONG = 86400  # 24 hours

# Rate limiting
RATE_LIMIT_REQUESTS_PER_MINUTE = 60
RATE_LIMIT_AI_REQUESTS_PER_HOUR = 100
RATE_LIMIT_IMAGE_GENERATIONS_PER_HOUR = 50

# Task timeouts (in seconds)
TASK_TIMEOUT_STORY_GENERATION = 300  # 5 minutes
TASK_TIMEOUT_IMAGE_GENERATION = 600  # 10 minutes
TASK_TIMEOUT_WEBTOON_COMPILATION = 1800  # 30 minutes

# WebSocket message types
WS_MESSAGE_TYPES = {
    "TASK_UPDATE": "task_update",
    "PANEL_UPDATE": "panel_update",
    "WEBTOON_UPDATE": "webtoon_update",
    "ERROR": "error",
    "CONNECTION_ESTABLISHED": "connection_established",
    "PING": "ping",
    "PONG": "pong",
}

# Supported AI models
SUPPORTED_LLM_MODELS = {"gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "claude-3-sonnet", "claude-3-haiku"}

SUPPORTED_IMAGE_MODELS = {
    "stable-diffusion-xl-1024-v1-0",
    "stable-diffusion-xl-beta-v2-2-2",
    "dall-e-3",
    "dall-e-2",
}

# Webtoon styles
WEBTOON_STYLES = {
    "webtoon": "Modern webtoon style with vibrant colors",
    "manga": "Traditional manga style in black and white",
    "comic": "Western comic book style with bold lines",
    "anime": "Anime-inspired art style",
    "realistic": "Photorealistic style",
}

# Character archetypes
CHARACTER_ARCHETYPES = {
    "protagonist": "Main character and hero of the story",
    "antagonist": "Primary opponent or villain",
    "mentor": "Wise guide who helps the protagonist",
    "sidekick": "Loyal companion to the protagonist",
    "love_interest": "Romantic interest of the protagonist",
    "comic_relief": "Character who provides humor",
    "neutral": "Neither clearly good nor evil",
}
