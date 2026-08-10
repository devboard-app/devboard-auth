from httpx import AsyncClient

from app.config import settings
from app.exceptions import CoreServiceException


async def sync_user_to_core(user_id: str, email: str, role: str)->None:
    payload={
        "user_id": user_id,
        "email": email,
        "role":role,
    }
    headers ={"X-Service-Key": settings.INTERNAL_API_KEY}
    async with AsyncClient() as client:
        response = await client.post(settings.CORE_SERVICE_URL, json=payload, headers=headers)
        if response.status_code != 201:
            raise CoreServiceException()