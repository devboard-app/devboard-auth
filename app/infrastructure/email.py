from app.config import settings
from app.exceptions import EmailServiceException
from app.infrastructure.http_client import get_http_client


async def send_verification_email(to: str, verify_url: str) -> None:
    payload ={
        "to": to,
        "subject":"Verify your email",
        "template":"verification",
        "variables":{
            "verification_link": verify_url 
        }
    }

    headers = {"X-Service-Key": settings.INTERNAL_API_KEY}
    response = await get_http_client().post(f'{settings.EMAIL_SERVICE_URL}/email/send', json=payload, headers=headers)
    if response.status_code != 200:
        raise EmailServiceException()