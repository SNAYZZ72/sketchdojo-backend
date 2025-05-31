# =============================================================================
# app/infrastructure/ai/image/stability_ai.py
# =============================================================================
import base64
import json
import logging
from typing import Any, Dict, Optional

import aiohttp

from .base import BaseImageGenerator, ImageRequest, ImageResponse, ImageStyle

logger = logging.getLogger(__name__)


class StabilityAIGenerator(BaseImageGenerator):
    """Stability AI image generator implementation."""

    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        self.base_url = "https://api.stability.ai"
        self.style_mappings = {
            ImageStyle.WEBTOON: "colorful webtoon style, clean lines, digital art",
            ImageStyle.MANGA: "black and white manga style, detailed line art",
            ImageStyle.COMIC: "comic book style, bold outlines, cel shading",
            ImageStyle.REALISTIC: "photorealistic, high detail",
            ImageStyle.ANIME: "anime style, cel shading, vibrant colors",
        }
        logger.info("Initialized Stability AI generator")

    def _enhance_prompt(self, prompt: str, style: ImageStyle) -> str:
        """Enhance prompt with style-specific elements."""
        style_enhancement = self.style_mappings.get(style, "")
        return f"{prompt}, {style_enhancement}, high quality, detailed"

    async def generate_image(self, request: ImageRequest) -> ImageResponse:
        """Generate image using Stability AI API."""
        try:
            enhanced_prompt = self._enhance_prompt(request.prompt, request.style)

            # Map quality to steps and cfg_scale
            quality_settings = {
                "draft": {"steps": 20, "cfg_scale": 5.0},
                "standard": {"steps": 30, "cfg_scale": 7.0},
                "high": {"steps": 50, "cfg_scale": 10.0},
                "ultra": {"steps": 80, "cfg_scale": 12.0},
            }

            settings = quality_settings.get(request.quality.value, quality_settings["standard"])

            payload = {
                "text_prompts": [{"text": enhanced_prompt, "weight": 1.0}],
                "cfg_scale": settings["cfg_scale"],
                "height": request.height,
                "width": request.width,
                "samples": 1,
                "steps": settings["steps"],
            }

            if request.negative_prompt:
                payload["text_prompts"].append({"text": request.negative_prompt, "weight": -1.0})

            if request.seed:
                payload["seed"] = request.seed

            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
                    json=payload,
                    headers=headers,
                ) as response:
                    if response.status == 200:
                        result = await response.json()

                        # Extract image data
                        image_data = base64.b64decode(result["artifacts"][0]["base64"])

                        # In a real implementation, you'd save this to storage
                        # and return a URL. For now, we'll return a placeholder URL
                        image_url = f"https://storage.sketchdojo.com/images/{result['artifacts'][0]['seed']}.png"

                        return ImageResponse(
                            image_url=image_url,
                            image_data=image_data,
                            seed=result["artifacts"][0].get("seed"),
                            metadata={
                                "provider": "stability_ai",
                                "model": "stable-diffusion-xl-1024-v1-0",
                                "prompt": enhanced_prompt,
                                "settings": settings,
                            },
                        )
                    else:
                        error_text = await response.text()
                        logger.error(f"Stability AI API error: {response.status} - {error_text}")
                        raise Exception(f"Image generation failed: {error_text}")

        except Exception as e:
            logger.error(f"Stability AI generation error: {str(e)}")
            raise

    async def upscale_image(self, image_url: str, scale_factor: int = 2) -> ImageResponse:
        """Upscale image using Stability AI."""
        # Implementation for image upscaling
        # This would involve downloading the image and sending it to the upscaling endpoint
        raise NotImplementedError("Image upscaling not yet implemented")
