"""Persistent ComfyUI configuration and workflow management."""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

DATA_ROOT = Path("data/comfyui")
WORKFLOW_ROOT = DATA_ROOT / "workflows"
SETTINGS_FILE = DATA_ROOT / "settings.json"


@dataclass
class ComfyUISettings:
    base_url: str = "http://127.0.0.1:8188"
    workflow_name: str = ""
    desktop_workflow_dir: str = ""
    positive_node_id: str = ""
    negative_node_id: str = ""
    seed_node_id: str = ""
    checkpoint_node_id: str = ""
    output_node_id: str = ""
    latent_node_id: str = ""
    library_workflow_id: str = "standard_checkpoint"
    checkpoint_name: str = ""
    developer_mode: str = "false"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ComfyUISettings":
        defaults = cls()
        return cls(
            **{
                key: str(data.get(key, getattr(defaults, key)) or "")
                for key in asdict(defaults).keys()
            }
        )

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


class ComfyUIManager:
    """Manage local ComfyUI settings and API-format workflow files."""

    @staticmethod
    def ensure_structure() -> None:
        WORKFLOW_ROOT.mkdir(parents=True, exist_ok=True)
        DATA_ROOT.mkdir(parents=True, exist_ok=True)

    @classmethod
    def load_settings(cls) -> ComfyUISettings:
        cls.ensure_structure()
        if not SETTINGS_FILE.exists():
            settings = ComfyUISettings()
            cls.save_settings(settings)
            return settings
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("ComfyUI settings must be a JSON object.")
            return ComfyUISettings.from_dict(data)
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return ComfyUISettings()

    @classmethod
    def save_settings(cls, settings: ComfyUISettings) -> Path:
        cls.ensure_structure()
        temporary = SETTINGS_FILE.with_suffix(".tmp")
        temporary.write_text(json.dumps(settings.to_dict(), indent=2), encoding="utf-8")
        temporary.replace(SETTINGS_FILE)
        return SETTINGS_FILE

    @classmethod
    def workflow_path(cls, workflow_name: str) -> Path:
        cls.ensure_structure()
        safe_name = Path(workflow_name).name
        if not safe_name.endswith(".json"):
            safe_name += ".json"
        return WORKFLOW_ROOT / safe_name

    @classmethod
    def list_workflows(cls) -> list[str]:
        cls.ensure_structure()
        return sorted(path.name for path in WORKFLOW_ROOT.glob("*.json") if path.is_file())

    @classmethod
    def import_workflow_bytes(cls, filename: str, content: bytes) -> str:
        cls.ensure_structure()
        try:
            data = json.loads(content.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError(f"Invalid workflow JSON: {error}") from error
        cls.validate_api_workflow(data)
        target = cls.workflow_path(filename)
        temporary = target.with_suffix(".tmp")
        temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        temporary.replace(target)

        # Import means use: select, analyze, map, and persist immediately.
        cls.auto_map(target.name)
        return target.name

    @classmethod
    def import_workflow_file(cls, source: Path) -> str:
        return cls.import_workflow_bytes(source.name, source.read_bytes())

    @classmethod
    def delete_workflow(cls, workflow_name: str) -> None:
        path = cls.workflow_path(workflow_name)
        if path.exists():
            path.unlink()

    @classmethod
    def load_workflow(cls, workflow_name: str) -> dict[str, Any]:
        path = cls.workflow_path(workflow_name)
        if not path.exists():
            raise FileNotFoundError(f"Workflow not found: {workflow_name}")
        data = json.loads(path.read_text(encoding="utf-8"))
        cls.validate_api_workflow(data)
        return data

    @staticmethod
    def validate_api_workflow(data: Any) -> None:
        if not isinstance(data, dict) or not data:
            raise ValueError("Workflow must be a non-empty JSON object.")
        node_count = 0
        for node_id, node in data.items():
            if not isinstance(node_id, str) or not isinstance(node, dict):
                continue
            if "class_type" in node and isinstance(node.get("inputs", {}), dict):
                node_count += 1
        if node_count == 0:
            raise ValueError(
                "This does not look like a ComfyUI API workflow. Export it using "
                "'Save (API Format)' or enable developer mode and export the API JSON."
            )

    @staticmethod
    def _node_text(node: dict[str, Any]) -> str:
        class_type = str(node.get("class_type", ""))
        meta = node.get("_meta", {})
        title = str(meta.get("title", "")) if isinstance(meta, dict) else ""
        return f"{class_type} {title}".lower()

    @classmethod
    def inspect_workflow(cls, workflow_name: str) -> dict[str, Any]:
        workflow = cls.load_workflow(workflow_name)
        nodes: list[dict[str, str]] = []
        text_candidates: list[str] = []
        positive_candidates: list[str] = []
        negative_candidates: list[str] = []
        checkpoint_candidates: list[str] = []
        sampler_candidates: list[str] = []
        output_candidates: list[str] = []
        latent_candidates: list[str] = []

        for node_id, node in workflow.items():
            if not isinstance(node, dict):
                continue
            node_id = str(node_id)
            class_type = str(node.get("class_type", ""))
            meta = node.get("_meta", {})
            title = str(meta.get("title", "")) if isinstance(meta, dict) else ""
            node_text = cls._node_text(node)
            inputs = node.get("inputs", {})
            inputs = inputs if isinstance(inputs, dict) else {}
            nodes.append({"id": node_id, "class_type": class_type, "title": title})

            is_text = "text" in inputs and (
                "cliptextencode" in class_type.lower()
                or "textencode" in class_type.lower()
                or "prompt" in node_text
                or "conditioning" in node_text
            )
            if is_text:
                text_candidates.append(node_id)
                if any(token in node_text for token in ("negative", "neg prompt", "negative prompt")):
                    negative_candidates.append(node_id)
                elif any(token in node_text for token in ("positive", "pos prompt", "prompt")):
                    positive_candidates.append(node_id)

            if "checkpointloader" in class_type.lower() or "unetloader" in class_type.lower():
                checkpoint_candidates.append(node_id)
            if "ksampler" in class_type.lower() or class_type in {"SamplerCustom", "SamplerCustomAdvanced"}:
                sampler_candidates.append(node_id)
            if class_type in {"SaveImage", "PreviewImage"} or "saveimage" in class_type.lower():
                output_candidates.append(node_id)
            if "latent" in class_type.lower() and ("width" in inputs or "height" in inputs):
                latent_candidates.append(node_id)

        # Titles are preferred. Fall back to the first/second text nodes.
        positive = positive_candidates[0] if positive_candidates else (text_candidates[0] if text_candidates else "")
        negative = negative_candidates[0] if negative_candidates else ""
        if not negative and len(text_candidates) > 1:
            negative = next((item for item in text_candidates if item != positive), "")

        return {
            "nodes": nodes,
            "text_nodes": text_candidates,
            "positive_nodes": positive_candidates,
            "negative_nodes": negative_candidates,
            "recommended_positive": positive,
            "recommended_negative": negative,
            "checkpoint_nodes": checkpoint_candidates,
            "sampler_nodes": sampler_candidates,
            "output_nodes": output_candidates,
            "latent_nodes": latent_candidates,
        }

    @classmethod
    def auto_map(cls, workflow_name: str) -> ComfyUISettings:
        current = cls.load_settings()
        info = cls.inspect_workflow(workflow_name)
        current.workflow_name = workflow_name
        current.library_workflow_id = ""
        current.positive_node_id = info["recommended_positive"]
        current.negative_node_id = info["recommended_negative"]
        current.checkpoint_node_id = info["checkpoint_nodes"][0] if info["checkpoint_nodes"] else ""
        current.seed_node_id = info["sampler_nodes"][0] if info["sampler_nodes"] else ""
        current.output_node_id = info["output_nodes"][0] if info["output_nodes"] else ""
        current.latent_node_id = info["latent_nodes"][0] if info["latent_nodes"] else ""
        cls.save_settings(current)
        return current

    @classmethod
    def activate_workflow(cls, workflow_name: str) -> ComfyUISettings:
        """Select, analyze, auto-map, and persist a workflow in one operation."""
        if workflow_name not in cls.list_workflows():
            raise FileNotFoundError(f"Workflow not found: {workflow_name}")
        return cls.auto_map(workflow_name)

    @classmethod
    def desktop_workflow_candidates(cls) -> list[Path]:
        """Return common ComfyUI Desktop workflow directories on macOS."""
        home = Path.home()
        candidates = [
            home / "Library/Application Support/ComfyUI/user/default/workflows",
            home / "Library/Application Support/ComfyUI/workflows",
            home / "Documents/ComfyUI/user/default/workflows",
            home / "Documents/ComfyUI/workflows",
            home / "ComfyUI/user/default/workflows",
        ]
        settings = cls.load_settings()
        if settings.desktop_workflow_dir:
            candidates.insert(0, Path(os.path.expanduser(settings.desktop_workflow_dir)))
        result: list[Path] = []
        seen: set[str] = set()
        for path in candidates:
            key = str(path.expanduser())
            if key not in seen:
                seen.add(key)
                result.append(path.expanduser())
        return result

    @classmethod
    def scan_desktop_workflows(cls, directory: str | Path | None = None) -> dict[str, Any]:
        """Import compatible API workflows from ComfyUI Desktop folders.

        Canvas-format files are reported as skipped because they cannot be queued through
        ComfyUI's HTTP API without an API-format export.
        """
        roots: Iterable[Path]
        if directory:
            root = Path(os.path.expanduser(str(directory))).expanduser()
            roots = [root]
            settings = cls.load_settings()
            settings.desktop_workflow_dir = str(root)
            cls.save_settings(settings)
        else:
            roots = cls.desktop_workflow_candidates()

        imported: list[str] = []
        skipped: list[str] = []
        errors: list[str] = []
        scanned_dirs: list[str] = []

        for root in roots:
            if not root.exists() or not root.is_dir():
                continue
            scanned_dirs.append(str(root))
            for source in sorted(root.rglob("*.json")):
                if not source.is_file():
                    continue
                try:
                    data = json.loads(source.read_text(encoding="utf-8-sig"))
                    cls.validate_api_workflow(data)
                    imported.append(cls.import_workflow_bytes(source.name, json.dumps(data).encode("utf-8")))
                except ValueError:
                    skipped.append(str(source))
                except (OSError, json.JSONDecodeError, UnicodeDecodeError) as error:
                    errors.append(f"{source}: {error}")

        return {
            "scanned_dirs": scanned_dirs,
            "imported": sorted(set(imported)),
            "skipped": skipped,
            "errors": errors,
        }

    @classmethod
    def build_prompt_workflow(
        cls,
        positive_prompt: str,
        negative_prompt: str,
        *,
        seed: int | None = None,
        checkpoint: str | None = None,
        profile: Any | None = None,
    ) -> dict[str, Any]:
        settings = cls.load_settings()
        if settings.library_workflow_id:
            from movie.workflow_library import WorkflowLibrary
            if not checkpoint:
                checkpoint = settings.checkpoint_name
            if not checkpoint:
                raise ValueError("Select an installed checkpoint first.")
            if seed is None:
                seed = 1
            if profile is None:
                raise ValueError("An image generation profile is required.")
            return WorkflowLibrary.build(
                settings.library_workflow_id,
                positive_prompt,
                negative_prompt,
                checkpoint=checkpoint,
                seed=int(seed),
                profile=profile,
            )
        if not settings.workflow_name:
            raise ValueError("No built-in or custom ComfyUI workflow is selected.")
        workflow = cls.load_workflow(settings.workflow_name)

        def set_input(node_id: str, key: str, value: Any) -> None:
            if not node_id:
                return
            node = workflow.get(node_id)
            if not isinstance(node, dict):
                raise ValueError(f"Mapped workflow node {node_id} does not exist.")
            inputs = node.setdefault("inputs", {})
            if not isinstance(inputs, dict):
                raise ValueError(f"Workflow node {node_id} has invalid inputs.")
            inputs[key] = value

        set_input(settings.positive_node_id, "text", positive_prompt)
        set_input(settings.negative_node_id, "text", negative_prompt)
        if seed is not None:
            node = workflow.get(settings.seed_node_id, {})
            key = "noise_seed" if node.get("class_type") == "KSamplerAdvanced" else "seed"
            set_input(settings.seed_node_id, key, int(seed))
        if checkpoint:
            node = workflow.get(settings.checkpoint_node_id, {})
            inputs = node.get("inputs", {}) if isinstance(node, dict) else {}
            checkpoint_key = "ckpt_name" if "ckpt_name" in inputs else "unet_name"
            set_input(settings.checkpoint_node_id, checkpoint_key, checkpoint)
        if profile is not None:
            sampler = workflow.get(settings.seed_node_id, {})
            sampler_inputs = sampler.get("inputs", {}) if isinstance(sampler, dict) else {}
            if isinstance(sampler_inputs, dict):
                if "steps" in sampler_inputs:
                    sampler_inputs["steps"] = int(profile.steps)
                if "cfg" in sampler_inputs:
                    sampler_inputs["cfg"] = float(profile.cfg)
            latent = workflow.get(settings.latent_node_id, {})
            latent_inputs = latent.get("inputs", {}) if isinstance(latent, dict) else {}
            if isinstance(latent_inputs, dict):
                if "width" in latent_inputs:
                    latent_inputs["width"] = int(profile.width)
                if "height" in latent_inputs:
                    latent_inputs["height"] = int(profile.height)
        return workflow
