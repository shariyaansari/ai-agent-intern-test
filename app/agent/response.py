from __future__ import annotations

from dataclasses import dataclass, field

from pydantic import BaseModel, Field


class SourceCitationModel(BaseModel):
    model_config = {
        "extra": "forbid",
    }

    document_id: str
    filename: str
    heading: str


class GeneratedResponse(BaseModel):
    model_config = {
        "extra": "forbid",
    }

    answer: str
    sources: list[SourceCitationModel]
    needs_human: bool


@dataclass
class SourceCitation:
    document_id: str
    filename: str
    heading: str


@dataclass
class AgentResponse:
    answer: str
    sources: list[SourceCitation] = field(
        default_factory=list
    )
    needs_human: bool = False