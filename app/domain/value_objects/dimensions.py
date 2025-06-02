# app/domain/value_objects/dimensions.py
"""
Panel dimensions value object
"""
from dataclasses import dataclass
from enum import Enum


class PanelSize(Enum):
    """Standard panel sizes"""

    FULL = "full"
    HALF = "half"
    THIRD = "third"
    QUARTER = "quarter"
    CUSTOM = "custom"


@dataclass(frozen=True)
class PanelDimensions:
    """Panel dimensions and layout configuration"""

    size: PanelSize = PanelSize.FULL
    width: int = 1024
    height: int = 1024
    aspect_ratio: str = "1:1"

    @classmethod
    def from_size(cls, size: PanelSize) -> "PanelDimensions":
        """Create dimensions from standard size"""
        size_configs = {
            PanelSize.FULL: cls(size, 1024, 1024, "1:1"),
            PanelSize.HALF: cls(size, 512, 1024, "1:2"),
            PanelSize.THIRD: cls(size, 341, 1024, "1:3"),
            PanelSize.QUARTER: cls(size, 256, 1024, "1:4"),
        }
        return size_configs.get(size, size_configs[PanelSize.FULL])

    @classmethod
    def custom(cls, width: int, height: int) -> "PanelDimensions":
        """Create custom dimensions"""
        aspect_ratio = f"{width}:{height}"
        return cls(PanelSize.CUSTOM, width, height, aspect_ratio)

    @property
    def total_pixels(self) -> int:
        """Get total pixel count"""
        return self.width * self.height
