"""Built-in ComfyUI workflow library owned by AI Movie Studio."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class WorkflowDefinition:
    id: str
    name: str
    description: str
    family: str
    recommended: bool
    positive_node_id: str
    negative_node_id: str
    sampler_node_id: str
    checkpoint_node_id: str
    latent_node_id: str
    output_node_id: str
    workflow: dict[str, Any]


_STANDARD_CHECKPOINT_WORKFLOW: dict[str, Any] = {
    "3": {
        "inputs": {
            "seed": 1,
            "steps": 20,
            "cfg": 6.0,
            "sampler_name": "euler",
            "scheduler": "normal",
            "denoise": 1.0,
            "model": ["4", 0],
            "positive": ["6", 0],
            "negative": ["7", 0],
            "latent_image": ["5", 0],
        },
        "class_type": "KSampler",
        "_meta": {"title": "Sampler"},
    },
    "4": {
        "inputs": {"ckpt_name": ""},
        "class_type": "CheckpointLoaderSimple",
        "_meta": {"title": "Checkpoint"},
    },
    "5": {
        "inputs": {"width": 768, "height": 768, "batch_size": 1},
        "class_type": "EmptyLatentImage",
        "_meta": {"title": "Image Size"},
    },
    "6": {
        "inputs": {"text": "", "clip": ["4", 1]},
        "class_type": "CLIPTextEncode",
        "_meta": {"title": "Positive Prompt"},
    },
    "7": {
        "inputs": {"text": "", "clip": ["4", 1]},
        "class_type": "CLIPTextEncode",
        "_meta": {"title": "Negative Prompt"},
    },
    "8": {
        "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
        "class_type": "VAEDecode",
        "_meta": {"title": "Decode"},
    },
    "9": {
        "inputs": {"filename_prefix": "AI_Movie_Studio", "images": ["8", 0]},
        "class_type": "SaveImage",
        "_meta": {"title": "Save Image"},
    },
}


WORKFLOWS: tuple[WorkflowDefinition, ...] = (
    WorkflowDefinition(
        id="standard_checkpoint",
        name="Standard Checkpoint",
        description="Built-in text-to-image workflow for SD 1.5, SDXL, and compatible single-checkpoint models.",
        family="checkpoint",
        recommended=True,
        positive_node_id="6",
        negative_node_id="7",
        sampler_node_id="3",
        checkpoint_node_id="4",
        latent_node_id="5",
        output_node_id="9",
        workflow=_STANDARD_CHECKPOINT_WORKFLOW,
    ),
)


class WorkflowLibrary:
    @staticmethod
    def list() -> tuple[WorkflowDefinition, ...]:
        return WORKFLOWS

    @staticmethod
    def get(workflow_id: str) -> WorkflowDefinition:
        return next((item for item in WORKFLOWS if item.id == workflow_id), WORKFLOWS[0])

    @classmethod
    def build(
        cls,
        workflow_id: str,
        positive_prompt: str,
        negative_prompt: str,
        *,
        checkpoint: str,
        seed: int,
        profile: Any,
    ) -> dict[str, Any]:
        definition = cls.get(workflow_id)
        workflow = deepcopy(definition.workflow)
        workflow[definition.positive_node_id]["inputs"]["text"] = positive_prompt
        workflow[definition.negative_node_id]["inputs"]["text"] = negative_prompt
        workflow[definition.sampler_node_id]["inputs"]["seed"] = int(seed)
        workflow[definition.sampler_node_id]["inputs"]["steps"] = int(profile.steps)
        workflow[definition.sampler_node_id]["inputs"]["cfg"] = float(profile.cfg)
        workflow[definition.checkpoint_node_id]["inputs"]["ckpt_name"] = checkpoint
        workflow[definition.latent_node_id]["inputs"]["width"] = int(profile.width)
        workflow[definition.latent_node_id]["inputs"]["height"] = int(profile.height)
        return workflow
