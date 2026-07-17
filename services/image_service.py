"""ComfyUI-backed image generation orchestration."""
from __future__ import annotations

import mimetypes
import random
import time
from pathlib import Path
from typing import Any

from movie.comfyui_manager import ComfyUIManager
from movie.image_studio import ImageRecord, get_profile, load_image_records, save_image_result
from movie.prompt_schema import PromptRecord
from movie.prompt_storage import load_latest_prompts
from services.comfyui_service import ComfyUIService


class ImageService:
    @staticmethod
    def load(project_name: str) -> list[ImageRecord]:
        return load_image_records(project_name)

    @staticmethod
    def _output_images(history: dict[str, Any], prompt_id: str) -> list[dict[str, str]]:
        entry = history.get(prompt_id, history)
        outputs = entry.get("outputs", {}) if isinstance(entry, dict) else {}
        images: list[dict[str, str]] = []
        if not isinstance(outputs, dict):
            return images
        for output in outputs.values():
            if not isinstance(output, dict):
                continue
            for item in output.get("images", []):
                if isinstance(item, dict) and item.get("filename"):
                    images.append({
                        "filename": str(item.get("filename", "")),
                        "subfolder": str(item.get("subfolder", "")),
                        "type": str(item.get("type", "output")),
                    })
        return images

    @classmethod
    def generate_shot(
        cls,
        project_name: str,
        prompt: PromptRecord,
        *,
        profile_id: str = "draft",
        checkpoint: str | None = None,
        seed: int | None = None,
        timeout_seconds: int = 900,
    ) -> ImageRecord:
        health = ComfyUIService.check()
        if not health.online:
            raise RuntimeError(health.message)
        settings = ComfyUIManager.load_settings()
        if not settings.library_workflow_id and not settings.workflow_name:
            raise ValueError("Select an image model first.")
        if not checkpoint:
            checkpoint = settings.checkpoint_name or None
        if settings.library_workflow_id and not checkpoint:
            raise ValueError("No installed checkpoint is selected.")
        profile = get_profile(profile_id)
        seed_value = int(seed if seed is not None else random.randint(1, 2_147_483_647))
        last_error: Exception | None = None
        for attempt in range(profile.retries + 1):
            try:
                response = ComfyUIService.queue_prompt(
                    prompt.prompt,
                    prompt.negative_prompt,
                    seed=seed_value + attempt,
                    checkpoint=checkpoint,
                    profile=profile,
                )
                prompt_id = str(response["prompt_id"])
                deadline = time.monotonic() + timeout_seconds
                while time.monotonic() < deadline:
                    history = ComfyUIService.history(prompt_id)
                    images = cls._output_images(history, prompt_id)
                    if images:
                        source = images[0]
                        content = ComfyUIService.download_image(**source)
                        suffix = Path(source["filename"]).suffix or mimetypes.guess_extension("image/png") or ".png"
                        record = ImageRecord(
                            scene_number=prompt.scene_number,
                            shot_number=prompt.shot_number,
                            filename="",
                            prompt_id=prompt_id,
                            seed=seed_value + attempt,
                            profile_id=profile.id,
                            workflow_name=settings.library_workflow_id or settings.workflow_name,
                            checkpoint=checkpoint or "",
                            prompt_version=prompt.version,
                            source_filename=source["filename"],
                            source_subfolder=source["subfolder"],
                            source_type=source["type"],
                        )
                        save_image_result(project_name, record, content, suffix)
                        return record
                    time.sleep(1.0)
                raise TimeoutError(f"ComfyUI image generation timed out after {timeout_seconds} seconds.")
            except Exception as error:  # noqa: BLE001 - retry remote generation failures
                last_error = error
        raise RuntimeError(f"Image generation failed after retries: {last_error}")

    @classmethod
    def generate_scene(
        cls,
        project_name: str,
        scene_number: int,
        *,
        profile_id: str = "draft",
        checkpoint: str | None = None,
        skip_existing: bool = True,
    ) -> list[ImageRecord]:
        prompts = [item for item in load_latest_prompts(project_name) if item.scene_number == scene_number]
        if not prompts:
            raise ValueError(f"No master prompts found for scene {scene_number}.")
        existing = {(item.scene_number, item.shot_number) for item in load_image_records(project_name)}
        results: list[ImageRecord] = []
        for prompt in prompts:
            if skip_existing and (prompt.scene_number, prompt.shot_number) in existing:
                continue
            results.append(cls.generate_shot(
                project_name,
                prompt,
                profile_id=profile_id,
                checkpoint=checkpoint,
            ))
        return results
