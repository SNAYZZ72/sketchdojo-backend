# app/infrastructure/image/image_processor.py
"""
Image processing utilities
"""
import logging
import os
from typing import Optional, Tuple

import aiofiles
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Utilities for image processing and manipulation"""

    def __init__(self, output_dir: str = "static/processed_images"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    async def create_placeholder_image(
        self,
        width: int,
        height: int,
        text: str = "Placeholder",
        filename: str = "placeholder.png",
    ) -> str:
        """Create a placeholder image with text"""
        try:
            # Create image
            image = Image.new("RGB", (width, height), color=(240, 240, 240))
            draw = ImageDraw.Draw(image)

            # Try to load a font
            try:
                font = ImageFont.load_default()
            except:
                font = None

            # Calculate text position
            if font:
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            else:
                text_width = len(text) * 8  # Rough estimate
                text_height = 16

            x = (width - text_width) // 2
            y = (height - text_height) // 2

            # Draw text
            draw.text((x, y), text, fill=(0, 0, 0), font=font)

            # Add border
            draw.rectangle([(0, 0), (width - 1, height - 1)], outline=(200, 200, 200))

            # Save image
            file_path = os.path.join(self.output_dir, filename)
            image.save(file_path, "PNG")

            logger.info(f"Created placeholder image: {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"Error creating placeholder image: {str(e)}")
            raise

    async def resize_image(
        self,
        input_path: str,
        output_path: str,
        target_width: int,
        target_height: int,
        maintain_aspect: bool = True,
    ) -> str:
        """Resize an image"""
        try:
            with Image.open(input_path) as image:
                if maintain_aspect:
                    image.thumbnail(
                        (target_width, target_height), Image.Resampling.LANCZOS
                    )
                else:
                    image = image.resize(
                        (target_width, target_height), Image.Resampling.LANCZOS
                    )

                # Ensure output directory exists
                os.makedirs(os.path.dirname(output_path), exist_ok=True)

                # Save resized image
                image.save(output_path, "PNG")

                logger.info(f"Resized image: {input_path} -> {output_path}")
                return output_path

        except Exception as e:
            logger.error(f"Error resizing image: {str(e)}")
            raise

    def validate_image_dimensions(
        self, width: int, height: int, max_width: int = 2048, max_height: int = 2048
    ) -> Tuple[int, int]:
        """Validate and constrain image dimensions"""
        if width > max_width:
            width = max_width
        if height > max_height:
            height = max_height

        if width < 64:
            width = 64
        if height < 64:
            height = 64

        return width, height

    async def add_watermark(
        self, input_path: str, output_path: str, watermark_text: str = "SketchDojo"
    ) -> str:
        """Add watermark to image"""
        try:
            with Image.open(input_path) as image:
                # Create a transparent overlay
                overlay = Image.new("RGBA", image.size, (255, 255, 255, 0))
                draw = ImageDraw.Draw(overlay)

                # Try to load a font
                try:
                    font = ImageFont.load_default()
                except:
                    font = None

                # Position watermark in bottom right
                if font:
                    bbox = draw.textbbox((0, 0), watermark_text, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                else:
                    text_width = len(watermark_text) * 8
                    text_height = 16

                x = image.width - text_width - 10
                y = image.height - text_height - 10

                # Draw watermark with transparency
                draw.text((x, y), watermark_text, fill=(255, 255, 255, 128), font=font)

                # Composite with original image
                if image.mode != "RGBA":
                    image = image.convert("RGBA")

                watermarked = Image.alpha_composite(image, overlay)

                # Save as PNG to preserve transparency
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                watermarked.save(output_path, "PNG")

                logger.info(f"Added watermark to image: {output_path}")
                return output_path

        except Exception as e:
            logger.error(f"Error adding watermark: {str(e)}")
            raise
