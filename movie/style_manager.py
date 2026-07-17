"""Local visual-style presets and project style selection."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from movie.production_manager import ProductionManager


@dataclass(frozen=True, slots=True)
class VisualStyle:
    id: str
    name: str
    description: str
    prompt_prefix: str
    prompt_suffix: str
    negative_prompt: str
    lighting: str
    color_palette: str
    contrast: str
    depth_of_field: str


DEFAULT_STYLES = (
    VisualStyle(
        id="cinematic_naturalism",
        name="Cinematic Naturalism",
        description="Grounded, realistic film stills with natural skin and practical lighting.",
        prompt_prefix="cinematic film still, grounded visual realism, natural human proportions",
        prompt_suffix="subtle film grain, realistic skin texture, production-quality composition",
        negative_prompt="plastic skin, oversaturated colors, artificial HDR, excessive sharpening",
        lighting="motivated practical lighting with soft natural falloff",
        color_palette="balanced earth tones with restrained highlights",
        contrast="medium cinematic contrast",
        depth_of_field="natural shallow depth of field when appropriate",
    ),
    VisualStyle(
        id="film_noir",
        name="Film Noir",
        description="High-contrast monochrome-inspired crime-drama imagery.",
        prompt_prefix="film noir cinematic still, dramatic shadows, moody urban atmosphere",
        prompt_suffix="hard light, graphic silhouettes, controlled highlights, fine film grain",
        negative_prompt="flat lighting, cheerful pastel palette, low contrast, glossy commercial look",
        lighting="hard directional key light with deep shadows",
        color_palette="black, charcoal, silver, restrained accent colors",
        contrast="high contrast",
        depth_of_field="selective focus with atmospheric depth",
    ),
    VisualStyle(
        id="warm_indie_drama",
        name="Warm Indie Drama",
        description="Intimate human storytelling with warm practical light and gentle texture.",
        prompt_prefix="intimate independent drama film still, emotionally observant framing",
        prompt_suffix="warm practical lighting, subtle grain, authentic lived-in detail",
        negative_prompt="blockbuster spectacle, neon overload, sterile studio background, glamour retouching",
        lighting="warm window light and practical lamps",
        color_palette="warm neutrals, muted amber, soft greens and browns",
        contrast="soft medium contrast",
        depth_of_field="gentle shallow depth of field",
    ),
    VisualStyle(
        id="stylized_animation",
        name="Stylized Animation",
        description="Original hand-crafted animated-film look without imitating a named studio.",
        prompt_prefix="original stylized animated film frame, expressive shapes, handcrafted visual design",
        prompt_suffix="cohesive color script, appealing silhouettes, cinematic composition",
        negative_prompt="photorealism, copied franchise characters, text, watermark, inconsistent anatomy",
        lighting="soft illustrative lighting with clear shape separation",
        color_palette="harmonious story-driven color palette",
        contrast="controlled graphic contrast",
        depth_of_field="layered illustrated depth",
    ),
    VisualStyle(
        id="neon_scifi",
        name="Neon Science Fiction",
        description="Atmospheric futuristic imagery with controlled neon accents.",
        prompt_prefix="cinematic science-fiction film still, futuristic environment, believable production design",
        prompt_suffix="volumetric atmosphere, controlled neon reflections, detailed practical surfaces",
        negative_prompt="random holographic text, unreadable signage, excessive neon, video-game HUD",
        lighting="motivated neon accents with cool ambient fill",
        color_palette="deep blue, cyan, magenta accents, neutral skin tones",
        contrast="medium-high contrast",
        depth_of_field="cinematic depth with atmospheric separation",
    ),
)


class StyleManager:
    @staticmethod
    def list_styles() -> list[VisualStyle]:
        return list(DEFAULT_STYLES)

    @staticmethod
    def get(style_id: str) -> VisualStyle:
        for style in DEFAULT_STYLES:
            if style.id == style_id:
                return style
        return DEFAULT_STYLES[0]

    @staticmethod
    def _settings_path(project_name: str) -> Path:
        return ProductionManager.ensure_structure(project_name) / "prompt_settings.json"

    @classmethod
    def get_project_style(cls, project_name: str) -> str:
        path = cls._settings_path(project_name)
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                style_id = str(data.get("style_id", "")).strip()
                if style_id:
                    return cls.get(style_id).id
            except (OSError, json.JSONDecodeError):
                pass
        return DEFAULT_STYLES[0].id

    @classmethod
    def set_project_style(cls, project_name: str, style_id: str) -> None:
        style = cls.get(style_id)
        path = cls._settings_path(project_name)
        path.write_text(
            json.dumps({"style_id": style.id, "style": asdict(style)}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
