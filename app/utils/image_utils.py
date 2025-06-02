"""
Image utility functions
"""
import logging
import os
from typing import Optional, Tuple

import aiofiles
from PIL import Image

logger = logging.getLogger(__name__)


def get_image_dimensions(image_path: str) -> Optional[Tuple[int, int]]:
    """Get image dimensions"""
    try:
        with Image.open(image_path) as img:
            return img.size
    except Exception as e:
        logger.error(f"Error getting image dimensions: {str(e)}")
        return None


def is_valid_image_format(filename: str) -> bool:
    """Check if filename has valid image format"""
    valid_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
    _, ext = os.path.splitext(filename.lower())
    return ext in valid_extensions


async def save_base64_image(base64_data: str, output_path: str) -> bool:
    """Save base64 image data to file"""
    try:
        import base64

        # Remove data URL prefix if present
        if "," in base64_data:
            base64_data = base64_data.split(",", 1)[1]

        # Decode and save
        image_data = base64.b64decode(base64_data)

        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        async with aiofiles.open(output_path, "wb") as f:
            await f.write(image_data)

        return True

    except Exception as e:
        logger.error(f"Error saving base64 image: {str(e)}")
        return False
