import argparse
import asyncio
import json

from tenant_packets.infrai_pdf import InfraiPdfClient
from tenant_packets.lifecycle_service import TenantPacketService
from tenant_packets.models import BundleRequest, LifecycleStage


async def run(args: argparse.Namespace) -> None:
    request = BundleRequest(
        tenant_id=args.tenant,
        stage=LifecycleStage(args.stage),
        source_pdfs=args.pdf,
        total_pages=args.pages,
    )
    client = InfraiPdfClient()
    try:
        result = await TenantPacketService(client).build(request)
        print(json.dumps(result.model_dump(mode="json"), indent=2))
    finally:
        await client.close()


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description="Build a tenant lifecycle PDF packet")
    command.add_argument("--tenant", required=True)
    command.add_argument(
        "--stage", choices=[stage.value for stage in LifecycleStage], required=True
    )
    command.add_argument("--pdf", action="append", required=True)
    command.add_argument("--pages", type=int, required=True)
    return command


if __name__ == "__main__":
    asyncio.run(run(parser().parse_args()))
