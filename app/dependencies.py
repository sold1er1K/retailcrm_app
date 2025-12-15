import httpx
from app.config import settings


async def get_retailcrm_client():
    async with httpx.AsyncClient(
        base_url=settings.retailcrm_url,
        headers={"X-API-KEY": settings.retailcrm_api_key},
        timeout=30.0
    ) as client:
        yield client
