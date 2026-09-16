from fastapi import Request

from app.config import settings


def get_client_ip(request: Request) -> str:
    trusted_proxies = settings.trusted_proxy_ips_set

    if request.client and request.client.host in trusted_proxies:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()

    return request.client.host if request.client else "unknown"