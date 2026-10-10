from fastapi import FastAPI, HTTPException

from .infrai_pdf import InfraiError, InfraiPdfClient
from .lifecycle_service import TenantPacketService
from .models import BundleRequest, BundleResult

app = FastAPI(title="Tenant lifecycle packet service")


@app.post("/tenant-packets", response_model=BundleResult)
async def build_tenant_packet(request: BundleRequest) -> BundleResult:
    client = InfraiPdfClient()
    try:
        return await TenantPacketService(client).build(request)
    except InfraiError as error:
        status = error.status_code if 400 <= error.status_code < 500 else 502
        raise HTTPException(
            status_code=status,
            detail={"code": error.code, "error": error.details},
        ) from error
    finally:
        await client.close()
