"""Provider interface shared by extraction and evidence assessment."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from pydantic import BaseModel

from ..schemas import ModelRun


@dataclass(frozen=True)
class ProviderStatus:
    provider: str
    state: str
    detail: str
    extraction_model: str | None = None
    assessment_model: str | None = None

    @property
    def available(self) -> bool:
        return self.state == "configured"


class ModelProvider(Protocol):
    def generate(
        self,
        output_type: type[BaseModel],
        task: str,
        payload: Any,
        *,
        system_instruction: str,
        task_instruction: str,
    ) -> tuple[BaseModel, ModelRun]: ...
