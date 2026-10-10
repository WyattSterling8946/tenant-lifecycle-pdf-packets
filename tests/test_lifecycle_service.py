import asyncio

from tenant_packets.lifecycle_service import TenantPacketService, plan_packets
from tenant_packets.models import BundleRequest, LifecycleStage


class RecordingPdfClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    async def merge(self, inputs: list[str], operation_id: str) -> dict[str, object]:
        self.calls.append(("merge", inputs))
        return {"pdf": "merged-tenant-pdf"}

    async def split(
        self, pdf: str, ranges: list[str], operation_id: str
    ) -> dict[str, object]:
        self.calls.append(("split", {"pdf": pdf, "ranges": ranges}))
        return {"parts": ["agreement", "admin-record"]}


def test_onboarding_packet_separates_agreement_from_admin_pages() -> None:
    plan = plan_packets(LifecycleStage.ONBOARDING, total_pages=5)
    assert plan.state == "onboarding_packet_ready"
    assert plan.ranges == ["1-2", "3-5"]


def test_service_merges_in_pipeline_order_then_splits_the_result() -> None:
    client = RecordingPdfClient()
    request = BundleRequest(
        tenant_id="tenant-204",
        stage=LifecycleStage.CLOSED,
        source_pdfs=["subscription-pdf", "admin-log-pdf"],
        total_pages=4,
    )

    result = asyncio.run(TenantPacketService(client).build(request))

    assert result.state == "closure_packet_ready"
    assert result.ranges == ["1-3", "4-4"]
    assert client.calls == [
        ("merge", ["subscription-pdf", "admin-log-pdf"]),
        (
            "split",
            {"pdf": "merged-tenant-pdf", "ranges": ["1-3", "4-4"]},
        ),
    ]
