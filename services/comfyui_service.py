"""Dependency-free ComfyUI HTTP API client and discovery service."""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from movie.comfyui_manager import ComfyUIManager


@dataclass(frozen=True)
class ComfyUIHealth:
    online: bool
    base_url: str
    message: str
    system_stats: dict[str, Any]


class ComfyUIService:
    @staticmethod
    def _base_url() -> str:
        return ComfyUIManager.load_settings().base_url.rstrip("/")

    @classmethod
    def _request_bytes(
        cls,
        path: str,
        *,
        method: str = "GET",
        payload: dict[str, Any] | None = None,
        timeout: float = 5.0,
    ) -> bytes:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(
            f"{cls._base_url()}{path}",
            data=body,
            method=method,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - local configured endpoint
            return response.read()

    @classmethod
    def _json_request(cls, path: str, *, method: str = "GET", payload=None, timeout: float = 5.0) -> dict[str, Any]:
        data = json.loads(cls._request_bytes(path, method=method, payload=payload, timeout=timeout).decode("utf-8"))
        return data if isinstance(data, dict) else {}

    @classmethod
    def check(cls, timeout: float = 3.0) -> ComfyUIHealth:
        base_url = cls._base_url()
        try:
            stats = cls._json_request("/system_stats", timeout=timeout)
        except (URLError, HTTPError, TimeoutError, json.JSONDecodeError, OSError) as error:
            return ComfyUIHealth(False, base_url, f"ComfyUI offline: {error}", {})
        devices = stats.get("devices", [])
        device_label = ""
        if isinstance(devices, list) and devices:
            device = devices[0] if isinstance(devices[0], dict) else {}
            device_label = str(device.get("name") or device.get("type") or "device")
        return ComfyUIHealth(True, base_url, f"ComfyUI ready{f' · {device_label}' if device_label else ''}", stats)

    @classmethod
    def object_info(cls) -> dict[str, Any]:
        return cls._json_request("/object_info", timeout=15.0)

    @classmethod
    def discover_models(cls) -> dict[str, list[str]]:
        info = cls.object_info()
        result = {"checkpoints": [], "vae": [], "loras": [], "controlnet": [], "upscale_models": []}
        mapping = {
            "CheckpointLoaderSimple": ("checkpoints", "ckpt_name"),
            "VAELoader": ("vae", "vae_name"),
            "LoraLoader": ("loras", "lora_name"),
            "ControlNetLoader": ("controlnet", "control_net_name"),
            "UpscaleModelLoader": ("upscale_models", "model_name"),
        }
        for class_type, (bucket, input_name) in mapping.items():
            node = info.get(class_type, {})
            required = node.get("input", {}).get("required", {}) if isinstance(node, dict) else {}
            spec = required.get(input_name, []) if isinstance(required, dict) else []
            values = spec[0] if isinstance(spec, list) and spec and isinstance(spec[0], list) else []
            result[bucket] = sorted(str(item) for item in values)
        return result

    @classmethod
    def queue_prompt(cls, positive_prompt: str, negative_prompt: str, *, seed=None, checkpoint=None, profile=None) -> dict[str, Any]:
        workflow = ComfyUIManager.build_prompt_workflow(
            positive_prompt, negative_prompt, seed=seed, checkpoint=checkpoint, profile=profile
        )
        response = cls._json_request(
            "/prompt", method="POST", payload={"prompt": workflow, "client_id": uuid.uuid4().hex}, timeout=30.0
        )
        if not response.get("prompt_id"):
            raise RuntimeError(f"ComfyUI did not return a prompt id: {response}")
        return response

    @classmethod
    def history(cls, prompt_id: str) -> dict[str, Any]:
        return cls._json_request(f"/history/{prompt_id}", timeout=15.0)

    @classmethod
    def download_image(cls, filename: str, subfolder: str = "", type: str = "output") -> bytes:
        query = urlencode({"filename": filename, "subfolder": subfolder, "type": type})
        return cls._request_bytes(f"/view?{query}", timeout=120.0)
