"""
Utility for rendering webtoons as HTML for frontend display
"""
import logging
from typing import Dict, List, Optional, Any
from uuid import UUID

from app.domain.entities.panel import Panel, SpeechBubble
from app.domain.entities.webtoon import Webtoon

logger = logging.getLogger(__name__)


class WebtoonRenderer:
    """Renders a webtoon as HTML for frontend display"""
    
    @staticmethod
    def render_webtoon(webtoon: Webtoon) -> str:
        """
        Renders a webtoon entity as HTML content
        
        Args:
            webtoon: The webtoon entity to render
            
        Returns:
            HTML string representation of the webtoon
        """
        if not webtoon:
            logger.warning("Cannot render null webtoon")
            return "<div class='webtoon-error'>No webtoon data available</div>"
            
        # Start with container
        html = f"""
        <div class="webtoon-container" data-webtoon-id="{webtoon.id}">
            <div class="webtoon-header">
                <h1 class="webtoon-title">{webtoon.title}</h1>
                <div class="webtoon-description">{webtoon.description}</div>
            </div>
            <div class="webtoon-panels">
        """
        
        # Sort panels by their position/order if available
        panels = sorted(webtoon.panels, key=lambda p: getattr(p, 'order', 0) if hasattr(p, 'order') else 0)
        
        # Render each panel
        for panel in panels:
            panel_html = WebtoonRenderer._render_panel(panel, webtoon.characters)
            html += panel_html
            
        # Close containers
        html += """
            </div>
        </div>
        """
        
        return html
    
    @staticmethod
    def _render_panel(panel: Panel, characters: List[Any]) -> str:
        """
        Renders a single panel as HTML
        
        Args:
            panel: The panel entity to render
            characters: List of characters for reference
            
        Returns:
            HTML string representation of the panel
        """
        # Panel container with data attributes for frontend interactivity
        html = f"""
        <div class="panel-container" data-panel-id="{panel.id}" data-art-style="{panel.art_style}">
            <div class="panel-image-container">
                <img 
                    src="{panel.image_url}" 
                    class="panel-image" 
                    alt="{panel.description or 'Webtoon panel'}"
                />
            </div>
        """
        
        # Add speech bubbles if any
        if panel.speech_bubbles and len(panel.speech_bubbles) > 0:
            html += """<div class="speech-bubbles-container">"""
            for bubble in panel.speech_bubbles:
                bubble_html = WebtoonRenderer._render_speech_bubble(bubble, characters)
                html += bubble_html
            html += """</div>"""
        
        # Panel description/metadata (hidden by default, can be shown via UI controls)
        html += f"""
            <div class="panel-metadata" style="display: none;">
                <div class="panel-description">{panel.description or ''}</div>
                <div class="panel-art-style">{panel.art_style or 'default'}</div>
            </div>
        </div>
        """
        
        return html
    
    @staticmethod
    def _render_speech_bubble(bubble: SpeechBubble, characters: List[Any]) -> str:
        """
        Renders a speech bubble as HTML
        
        Args:
            bubble: The speech bubble entity to render
            characters: List of characters for reference
            
        Returns:
            HTML string representation of the speech bubble
        """
        # Find character by name if available
        character_name = bubble.character_name or "Unknown"
        character_color = "default"
        
        # Try to find matching character for color coding
        for character in characters:
            if character.name.lower() == character_name.lower():
                # Use character hair color or some other distinctive feature for the bubble styling
                if hasattr(character, 'appearance') and character.appearance:
                    if hasattr(character.appearance, 'hair_color') and character.appearance.hair_color:
                        character_color = character.appearance.hair_color.lower().replace(' ', '-')
                break
        
        # Determine bubble type CSS class
        bubble_type_class = "speech"
        if bubble.bubble_type:
            if bubble.bubble_type.lower() == "thought":
                bubble_type_class = "thought"
            elif bubble.bubble_type.lower() == "narration":
                bubble_type_class = "narration"
        
        # Determine position class
        position_class = "top-right"
        if bubble.position:
            position_class = bubble.position
            
        # Render the bubble with appropriate classes
        html = f"""
        <div 
            class="speech-bubble {bubble_type_class} {position_class}" 
            data-bubble-id="{bubble.id}" 
            data-character="{character_name}" 
            data-character-color="{character_color}"
        >
            <div class="bubble-character-name">{character_name}</div>
            <div class="bubble-text">{bubble.text}</div>
        </div>
        """
        
        return html
        
    @staticmethod
    def render_css_styles() -> str:
        """
        Generate CSS styles for webtoon rendering
        
        Returns:
            CSS styles as a string
        """
        return """
        <style>
        .webtoon-container {
            font-family: 'Comic Sans MS', 'Segoe UI', sans-serif;
            max-width: 800px;
            margin: 0 auto;
            background-color: white;
        }
        
        .webtoon-header {
            padding: 20px;
            text-align: center;
            border-bottom: 3px solid #eee;
            margin-bottom: 20px;
        }
        
        .webtoon-title {
            font-size: 2.5em;
            margin-bottom: 10px;
            color: #333;
        }
        
        .webtoon-description {
            color: #666;
            font-style: italic;
        }
        
        .webtoon-panels {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        
        .panel-container {
            position: relative;
            margin-bottom: 20px;
            border-radius: 5px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        
        .panel-image-container {
            position: relative;
        }
        
        .panel-image {
            width: 100%;
            display: block;
        }
        
        .speech-bubbles-container {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
        }
        
        .speech-bubble {
            position: absolute;
            background-color: white;
            border-radius: 20px;
            padding: 10px 15px;
            max-width: 40%;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
            pointer-events: auto;
        }
        
        .speech-bubble.top-left {
            top: 10px;
            left: 10px;
        }
        
        .speech-bubble.top-right {
            top: 10px;
            right: 10px;
        }
        
        .speech-bubble.bottom-left {
            bottom: 10px;
            left: 10px;
        }
        
        .speech-bubble.bottom-right {
            bottom: 10px;
            right: 10px;
        }
        
        .speech-bubble.center {
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
        }
        
        .bubble-character-name {
            font-weight: bold;
            font-size: 0.8em;
            margin-bottom: 5px;
            color: #555;
        }
        
        .bubble-text {
            font-size: 1em;
            line-height: 1.4;
        }
        
        .speech-bubble.thought {
            border-radius: 30px;
            background-color: #f8f8f8;
        }
        
        .speech-bubble.thought .bubble-text:before {
            content: '💭 ';
        }
        
        .speech-bubble.narration {
            background-color: rgba(255, 255, 200, 0.9);
            font-style: italic;
        }
        
        /* Character color coding examples */
        .speech-bubble[data-character-color="red"] { border-left: 4px solid #ff6b6b; }
        .speech-bubble[data-character-color="blue"] { border-left: 4px solid #4dabf7; }
        .speech-bubble[data-character-color="green"] { border-left: 4px solid #51cf66; }
        .speech-bubble[data-character-color="purple"] { border-left: 4px solid #cc5de8; }
        .speech-bubble[data-character-color="black"] { border-left: 4px solid #343a40; }
        .speech-bubble[data-character-color="blonde"] { border-left: 4px solid #ffd43b; }
        .speech-bubble[data-character-color="brown"] { border-left: 4px solid #a98467; }
        </style>
        """
