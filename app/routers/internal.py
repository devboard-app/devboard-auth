import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import verify_internal_key
from app.schemas.auth import UpdateUserStatusRequest
from app.services.auth import update_user_status as update_user_status_serv

router = APIRouter(
    prefix="/internal",
    tags=["internal"],
)

@router.patch("/users/{user_id}/status/", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(verify_internal_key)])
async def update_user_status(user_id: uuid.UUID, request: UpdateUserStatusRequest, db: AsyncSession= Depends(get_db)):
    await update_user_status_serv(user_id, request.is_active, db)
