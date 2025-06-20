"""
Setup module for WebSocket handlers and tools
"""
import logging
from typing import List

from app.application.services.generation_service import GenerationService
from app.application.services.webtoon_service import WebtoonService
from app.dependencies import get_generation_service, get_webtoon_service
from app.websocket.handlers.tool_handler import get_tool_handler
from app.websocket.handlers.webtoon_tools import register_webtoon_tools

logger = logging.getLogger(__name__)


async def setup_websocket_tools() -> List[str]:
    """Initialize and register all tools with the tool handler"""
    # Get services
    generation_service = get_generation_service()
    webtoon_service = get_webtoon_service()
    
    # Get tool handler
    tool_handler = get_tool_handler()
    
    # Register webtoon tools
    register_webtoon_tools(tool_handler, generation_service, webtoon_service)
    
    # List all available tool IDs
    available_tools = [tool.tool_id for tool in tool_handler.tool_registry.tools.values()]
    logger.info(f"Available WebSocket tools: {', '.join(available_tools)}")
    
    return available_tools
