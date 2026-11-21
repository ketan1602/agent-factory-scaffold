from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

KNOWN_TOOLS = frozenset({"create_ticket", "add_note", "issue_refund", "delete_customer"})


class Metadata(BaseModel):
    name: str = Field(pattern=r"^[a-z][a-z0-9-]{1,62}$")
    version: str
    owner: str


class Tools(BaseModel):
    allow: list[str] = Field(min_length=1)


class Budget(BaseModel):
    maxTokens: int = Field(gt=0)
    maxCostUsd: float = Field(gt=0)


class Approval(BaseModel):
    refundAboveAmount: float = Field(ge=0)
    approvers: list[str] = Field(min_length=1)


class Evaluation(BaseModel):
    cases: str
    minimumPassRate: float = Field(ge=0, le=1)
    criticalViolationsAllowed: int = Field(ge=0)


class Spec(BaseModel):
    runtime: str
    scope: str
    tools: Tools
    budget: Budget
    approval: Approval
    evaluation: Evaluation


class Manifest(BaseModel):
    apiVersion: Literal["agents.enterprise/v1"]
    kind: Literal["Agent"]
    metadata: Metadata
    spec: Spec

    def unknown_tools(self) -> list[str]:
        return sorted(set(self.spec.tools.allow) - KNOWN_TOOLS)


def load_manifest(path: Path) -> Manifest:
    manifest = Manifest.model_validate(yaml.safe_load(path.read_text()))
    if unknown := manifest.unknown_tools():
        raise ValueError(f"{path.name}: unknown tools {unknown}")
    return manifest


def load_manifests(directory: Path) -> list[Manifest]:
    return [load_manifest(p) for p in sorted(directory.glob("*.yaml"))]
