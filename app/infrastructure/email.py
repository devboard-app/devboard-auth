from httpx import AsyncClient
from app.config import settings
from app.exceptions import EmailServiceException

async def send_verification_email(to: str, verify_url: str) -> None:
    payload ={
        "to": to,
        "subject":"Verify your email",
        "template":"verification",
        "variables":{
            "verification_link": verify_url 
        }
    }

    async with AsyncClient() as client:
        response = await client.post(settings.MAIL_SERVICE_URL, json=payload)
        if response.status_code != 200:
            raise EmailServiceException()