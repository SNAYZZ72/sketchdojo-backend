# app/utils/constants.py
"""
Application constants
"""

# Art Styles
ART_STYLES = [
    "manga",
    "webtoon",
    "comic",
    "anime",
    "realistic",
    "sketch",
    "chibi",
]

# Panel Sizes
PANEL_SIZES = ["full", "half", "third", "quarter"]

# Task Statuses
TASK_STATUSES = ["pending", "processing", "completed", "failed", "cancelled"]

# Task Types
TASK_TYPES = [
    "webtoon_generation",
    "panel_generation",
    "image_generation",
    "story_generation",
]

# Speech Bubble Styles
SPEECH_BUBBLE_STYLES = ["normal", "thought", "shout", "whisper"]

# Camera Angles
CAMERA_ANGLES = [
    "close-up",
    "medium",
    "wide",
    "bird's-eye",
    "worm's-eye",
    "dutch-angle",
]

# Moods
COMMON_MOODS = [
    "happy",
    "sad",
    "angry",
    "excited",
    "calm",
    "tense",
    "mysterious",
    "romantic",
    "dramatic",
    "comedic",
    "action-packed",
    "peaceful",
]

# Image Generation
DEFAULT_IMAGE_WIDTH = 1024
DEFAULT_IMAGE_HEIGHT = 1024
MAX_IMAGE_WIDTH = 2048
MAX_IMAGE_HEIGHT = 2048

# Generation Limits
MAX_PANELS_PER_WEBTOON = 20
MAX_CHARACTERS_PER_WEBTOON = 10
MAX_SPEECH_BUBBLES_PER_PANEL = 5

# Text Limits
MAX_PROMPT_LENGTH = 2000
MAX_TITLE_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 2000
MAX_CHARACTER_NAME_LENGTH = 100
MAX_DIALOGUE_LENGTH = 500

# Cache Keys
CACHE_KEY_WEBTOON = "webtoon:{id}"
CACHE_KEY_TASK = "task:{id}"
CACHE_KEY_USER_TASKS = "user:{user_id}:tasks"

# WebSocket Events
WS_EVENT_TASK_UPDATE = "task_update"
WS_EVENT_GENERATION_PROGRESS = "generation_progress"
WS_EVENT_GENERATION_COMPLETED = "generation_completed"
WS_EVENT_GENERATION_FAILED = "generation_failed"
WS_EVENT_PANEL_GENERATED = "panel_generated"

# HTTP Status Codes
HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_400_BAD_REQUEST = 400
HTTP_401_UNAUTHORIZED = 401
HTTP_403_FORBIDDEN = 403
HTTP_404_NOT_FOUND = 404
HTTP_422_UNPROCESSABLE_ENTITY = 422
HTTP_500_INTERNAL_SERVER_ERROR = 500

# Rate Limits
RATE_LIMIT_GENERATION = "5/minute"
RATE_LIMIT_API = "100/minute"
RATE_LIMIT_WEBSOCKET = "1000/minute"

# File Paths
STATIC_DIR = "static"
IMAGES_DIR = "static/images"
GENERATED_IMAGES_DIR = "static/generated_images"
TEMP_DIR = "static/temp"

# Timeouts (seconds)
AI_REQUEST_TIMEOUT = 60
IMAGE_GENERATION_TIMEOUT = 120
WEBSOCKET_TIMEOUT = 30
TASK_TIMEOUT = 1800  # 30 minutes

# Health Check
HEALTH_CHECK_TIMEOUT = 5  # seconds
