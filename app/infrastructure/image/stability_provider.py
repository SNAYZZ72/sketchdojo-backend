# app/infrastructure/image/stability_provider.py
"""
Stability AI provider implementation
"""
import base64
import logging
import os
from datetime import datetime
from typing import Optional, Tuple

import aiofiles
import aiohttp

from app.application.interfaces.image_generator import ImageGenerator

logger = logging.getLogger(__name__)


class StabilityProvider(ImageGenerator):
    """Stability AI implementation of image generator interface"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: str = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
    ):
        self.api_key = api_key
        self.api_url = api_url
        # Store in shared volume path that both containers can access
        self.output_dir = "/app/storage/generated_images"
        self.base_url = "http://localhost:8000"  # This should come from config

        # Ensure output directory exists with proper permissions
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            # Ensure both containers can read/write to this directory
            os.chmod(self.output_dir, 0o777)
            logger.info(f"Output directory {self.output_dir} configured with shared permissions")
        except Exception as e:
            logger.error(f"Error setting up output directory: {str(e)}")
            logger.warning("Falling back to default location if shared volume is not accessible")

        if self.api_key:
            logger.info("Stability AI provider initialized with API key")
        else:
            logger.warning(
                "Stability AI provider initialized without API key - will use placeholders"
            )

    async def generate_image(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        style: str = "webtoon",
    ) -> Tuple[str, str]:
        """Generate an image from a prompt"""
        logger.debug(f"StabilityProvider.generate_image called with prompt: {prompt[:30]}..., style: {style}")
        
        is_available = await self.is_available()
        if not is_available:
            logger.info(f"StabilityProvider not available (API key missing), generating placeholder image")
            result = await self._generate_placeholder_image(prompt, width, height)
            logger.debug(f"Placeholder image result type: {type(result)}, content: {result}")
            return result

        try:
            style_modifiers = self._get_style_modifiers(style)
            logger.debug(f"Style modifiers for {style}: {style_modifiers}")
            enhanced_prompt = await self.enhance_prompt(prompt, style_modifiers)
            logger.debug(f"Enhanced prompt: {enhanced_prompt[:50]}...")

            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }
            logger.debug(f"API key configured: {self.api_key is not None}")

            # Ensure dimensions are valid for SDXL
            original_dims = (width, height)
            width, height = self._normalize_dimensions(width, height)
            logger.debug(f"Normalized dimensions from {original_dims} to {(width, height)}")

            payload = {
                "text_prompts": [{"text": enhanced_prompt, "weight": 1.0}],
                "cfg_scale": 7,
                "height": height,
                "width": width,
                "samples": 1,
                "steps": 30,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url, json=payload, headers=headers
                ) as response:
                    if response.status == 200:
                        response_data = await response.json()

                        if "artifacts" in response_data and response_data["artifacts"]:
                            image_data = response_data["artifacts"][0]["base64"]
                            logger.info("Successfully received image data from Stability API")
                            result = await self._save_image(image_data, prompt)
                            logger.debug(f"Image save result: {type(result)}, content: {result}")
                            return result
                        else:
                            logger.error("No image artifacts in response")
                            return await self._generate_placeholder_image(prompt, width, height)
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"Stability API error ({response.status}): {error_text}"
                        )
                        logger.error("Falling back to placeholder image due to error in API call")
                        result = await self._generate_placeholder_image(prompt, width, height)
                        logger.debug(f"Placeholder image result from API error: {type(result)}, content: {result}")
                        return result

        except Exception as e:
            logger.error(f"Error generating image: {str(e)}")
            logger.exception("Full traceback:")
            result = await self._generate_placeholder_image(prompt, width, height)
            logger.debug(f"Placeholder image result from exception: {type(result)}, content: {result}")
            return result

    async def enhance_prompt(self, base_prompt: str, style_modifiers: str) -> str:
        """Enhance a prompt with style-specific modifiers"""
        # Truncate if too long
        max_length = 1800  # Leave room for style modifiers
        if len(base_prompt) > max_length:
            base_prompt = base_prompt[:max_length] + "..."

        enhanced = f"{style_modifiers}, {base_prompt}"

        # Add quality modifiers
        quality_modifiers = "high quality, detailed, professional artwork"
        enhanced = f"{enhanced}, {quality_modifiers}"

        return enhanced

    async def is_available(self) -> bool:
        """Check if the image generator is available"""
        available = self.api_key is not None
        logger.debug(f"StabilityProvider.is_available() returning {available}")
        return available

    def _get_style_modifiers(self, style: str) -> str:
        """Get style-specific modifiers for prompts"""
        style_map = {
            "webtoon": "webtoon style, digital art, clean lines, vibrant colors, korean manhwa style",
            "manga": "manga style, black and white, detailed linework, screentone shading",
            "comic": "comic book style, bold outlines, flat colors, dynamic composition",
            "anime": "anime style, cel shading, bright colors, japanese animation style",
            "realistic": "realistic style, photorealistic, detailed textures, natural lighting",
            "sketch": "sketch style, hand-drawn, pencil lines, artistic sketch",
        }
        return style_map.get(style, style_map["webtoon"])

    def _normalize_dimensions(self, width: int, height: int) -> Tuple[int, int]:
        """Normalize dimensions to valid SDXL sizes"""
        # Valid SDXL dimensions
        valid_dimensions = [
            (1024, 1024),
            (1152, 896),
            (1216, 832),
            (1344, 768),
            (1536, 640),
            (640, 1536),
            (768, 1344),
            (832, 1216),
            (896, 1152),
        ]

        # Find closest valid dimensions
        target_ratio = width / height
        best_match = min(
            valid_dimensions, key=lambda d: abs(d[0] / d[1] - target_ratio)
        )

        return best_match

    async def _save_image(self, base64_data: str, prompt: str) -> Tuple[str, str]:
        """Save base64 image data to file"""
        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_prompt = "".join(
                c for c in prompt[:30] if c.isalnum() or c in (" ", "-", "_")
            ).strip()
            safe_prompt = safe_prompt.replace(" ", "_")
            filename = f"{timestamp}_{safe_prompt}.png"

            # Full file path
            file_path = os.path.join(self.output_dir, filename)

            # Decode and save
            image_bytes = base64.b64decode(base64_data)
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(image_bytes)

            # Generate public URL - we still serve at the same public path
            # even though we're storing in a different location internally
            public_url = f"{self.base_url}/static/generated_images/{filename}"

            logger.info(f"Image saved: {file_path}")
            return file_path, public_url

        except Exception as e:
            logger.error(f"Error saving image: {str(e)}")
            return await self._generate_placeholder_image(prompt, 1024, 1024)

    async def _generate_placeholder_image(
        self, prompt: str, width: int, height: int
    ) -> Tuple[str, str]:
        """Generate a placeholder image"""
        try:
            from PIL import Image, ImageDraw, ImageFont

            # Create placeholder image
            image = Image.new("RGB", (width, height), color=(240, 240, 240))
            draw = ImageDraw.Draw(image)

            # Add text
            try:
                font = ImageFont.load_default()
            except Exception:
                font = None

            text_lines = [
                "Placeholder Image",
                f"Prompt: {prompt[:50]}...",
                f"Size: {width}x{height}",
            ]

            y_offset = height // 2 - 30
            for line in text_lines:
                if font:
                    bbox = draw.textbbox((0, 0), line, font=font)
                    text_width = bbox[2] - bbox[0]
                    x_offset = (width - text_width) // 2
                    draw.text((x_offset, y_offset), line, fill=(0, 0, 0), font=font)
                y_offset += 25

            # Save placeholder
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"placeholder_{timestamp}.png"
            file_path = os.path.join(self.output_dir, filename)

            image.save(file_path, "PNG")

            public_url = f"{self.base_url}/static/generated_images/{filename}"

            return file_path, public_url

        except Exception as e:
            logger.error(f"Error creating placeholder: {str(e)}")
            # Return a basic placeholder path
            return "placeholder.png", f"{self.base_url}/static/placeholder.png"
