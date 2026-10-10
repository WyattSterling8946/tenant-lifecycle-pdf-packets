from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class LifecycleStage(StrEnum):
    ONBOARDING = "onboarding"
    ACTIVE = "active"
    CLOSED = "closed"


class BundleRequest(BaseModel):
    tenant_id: str = Field(min_length=1)
    stage: LifecycleStage
    source_pdfs: list[str] = Field(min_length=2)
    total_pages: int = Field(gt=0)

    @field_validator("source_pdfs")
    @classmethod
    def source_order_is_unambiguous(cls, value: list[str]) -> list[str]:
        if len(set(value)) != len(value):
            raise ValueError("source_pdfs must not contain duplicates")
        return value


class BundleResult(BaseModel):
    tenant_id: str
    stage: LifecycleStage
    state: str
    ranges: list[str]
    merged: dict[str, object]
    packets: dict[str, object]
