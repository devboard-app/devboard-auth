from app.config import settings
from app.exceptions import CoreServiceException
from app.infrastructure.http_client import get_http_client


async def sync_user_to_core(user_id: str, email: str, role: str)->None:
    payload={
        "user_id": user_id,
        "email": email,
        "role":role,
    }
    headers ={"X-Service-Key": settings.INTERNAL_API_KEY}
    response = await get_http_client().post(f'{settings.CORE_SERVICE_URL}/api/users/sync/', json=payload, headers=headers)
    if response.status_code not in (200, 201):
        raise CoreServiceException()

