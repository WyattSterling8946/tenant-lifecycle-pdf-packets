from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from .models import BundleRequest, BundleResult, LifecycleStage


@dataclass(frozen=True)
class PacketPlan:
    state: str
    ranges: list[str]


def plan_packets(stage: LifecycleStage, total_pages: int) -> PacketPlan:
    if stage is LifecycleStage.ONBOARDING:
        boundary = min(2, total_pages)
        ranges = [f"1-{boundary}"]
        if total_pages > boundary:
            ranges.append(f"{boundary + 1}-{total_pages}")
        return PacketPlan("onboarding_packet_ready", ranges)
    if stage is LifecycleStage.ACTIVE:
        return PacketPlan("account_review_packet_ready", [f"1-{total_pages}"])

    boundary = max(1, total_pages - 1)
    ranges = [f"1-{boundary}"]
    if total_pages > 1:
        ranges.append(f"{total_pages}-{total_pages}")
    return PacketPlan("closure_packet_ready", ranges)


class TenantPacketService:
    def __init__(self, pdf: Any) -> None:
        self._pdf = pdf

    async def build(self, request: BundleRequest) -> BundleResult:
        plan = plan_packets(request.stage, request.total_pages)
        run_id = f"tenant:{request.tenant_id}:{uuid4()}"
        merged = await self._pdf.merge(request.source_pdfs, run_id)
        pdf = merged.get("pdf")
        if not isinstance(pdf, str) or not pdf:
            raise ValueError("merge response requires a pdf reference")
        packets = await self._pdf.split(pdf, plan.ranges, run_id)
        return BundleResult(
            tenant_id=request.tenant_id,
            stage=request.stage,
            state=plan.state,
            ranges=plan.ranges,
            merged=merged,
            packets=packets,
        )
