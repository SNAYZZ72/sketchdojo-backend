# app/domain/value_objects/position.py
"""
Position value object for element placement
"""
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Position:
    """2D position with percentage-based coordinates"""

    x_percent: float = 50.0  # 0-100
    y_percent: float = 50.0  # 0-100
    anchor: str = "center"  # top-left, top-center, top-right, etc.

    def __post_init__(self):
        if not (0 <= self.x_percent <= 100):
            raise ValueError("x_percent must be between 0 and 100")
        if not (0 <= self.y_percent <= 100):
            raise ValueError("y_percent must be between 0 and 100")

    @classmethod
    def from_named_position(cls, position_name: str) -> "Position":
        """Create position from named location"""
        positions = {
            "top-left": cls(10, 10, "top-left"),
            "top-center": cls(50, 10, "top-center"),
            "top-right": cls(90, 10, "top-right"),
            "center-left": cls(10, 50, "center-left"),
            "center": cls(50, 50, "center"),
            "center-right": cls(90, 50, "center-right"),
            "bottom-left": cls(10, 90, "bottom-left"),
            "bottom-center": cls(50, 90, "bottom-center"),
            "bottom-right": cls(90, 90, "bottom-right"),
        }
        return positions.get(position_name, positions["center"])

    def to_css_style(self) -> str:
        """Convert to CSS positioning"""
        return f"left: {self.x_percent}%; top: {self.y_percent}%;"

    def to_coordinates(self, canvas_width: int, canvas_height: int) -> Tuple[int, int]:
        """Convert to absolute coordinates"""
        x = int((self.x_percent / 100) * canvas_width)
        y = int((self.y_percent / 100) * canvas_height)
        return x, y
