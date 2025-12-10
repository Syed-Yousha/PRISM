from manim import *
from .theme import * # Import your brand colors

class PrismSlide(VGroup):
    """
    A standard slide layout with a Title and Body.
    Automatic positioning and text wrapping.
    """
    def __init__(self, title_text, body_text=None, **kwargs):
        super().__init__(**kwargs)
        
        # 1. Create Title
        self.title = Text(title_text, font_size=TITLE_SIZE, color=PRIMARY_COLOR)
        self.title.to_edge(UP)
        self.add(self.title)
        
        # 2. Create Body (if exists)
        if body_text:
            self.body = Text(body_text, font_size=BODY_SIZE, color=TEXT_COLOR, line_spacing=1.3)
            self.body.width = 11  # Constrain width to fit screen
            self.body.next_to(self.title, DOWN, buff=1.0)
            self.add(self.body)
        else:
            self.body = None

    def animate_intro(self):
        """Returns the animation group to introduce this slide."""
        anims = [Write(self.title)]
        if self.body:
            anims.append(FadeIn(self.body, shift=UP))
        
        return AnimationGroup(*anims, lag_ratio=0.5)


class PrismDefinitionBox(VGroup):
    """
    A fancy box for important definitions or formulas.
    """
    def __init__(self, label, content, **kwargs):
        super().__init__(**kwargs)
        
        # The content text/math
        self.content = Tex(content, font_size=36, color=TEXT_COLOR)
        
        # The label (e.g., "Theorem")
        self.label = Text(label, font_size=24, color=ACCENT_COLOR)
        self.label.next_to(self.content, UP, aligned_edge=LEFT)
        
        # The Box
        self.box = SurroundingRectangle(
            VGroup(self.content, self.label), 
            color=PRIMARY_COLOR, 
            buff=0.3,
            fill_opacity=0.1,
            fill_color=PRIMARY_COLOR
        )
        
        self.add(self.box, self.label, self.content)

    def create(self):
        return AnimationGroup(
            Create(self.box),
            Write(self.label),
            Write(self.content),
            lag_ratio=0.2
        )