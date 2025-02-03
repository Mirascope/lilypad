"""The `/device_codes` API router."""

from typing import Annotated

from fastapi import APIRouter, Depends

from ..._utils import create_jwt_token, get_current_user
from ...models import DeviceCodeTable
from ...schemas import UserPublic
from ...services import DeviceCodeService

device_codes_api = APIRouter()


@device_codes_api.get("/device-codes/{device_code}", response_model=DeviceCodeTable)
async def get_device_code(
    device_code: str,
    device_code_service: Annotated[DeviceCodeService, Depends(DeviceCodeService)],
) -> DeviceCodeTable:
    """Get a device code."""
    return device_code_service.find_record_by_id(device_code)


@device_codes_api.post("/device-codes/{device_code}", response_model=DeviceCodeTable)
async def post_device_code(
    device_code: str,
    user: Annotated[UserPublic, Depends(get_current_user)],
    device_code_service: Annotated[DeviceCodeService, Depends(DeviceCodeService)],
) -> DeviceCodeTable:
    """Get a device code."""
    token = create_jwt_token(user)
    return device_code_service.create_record(device_code, token)


@device_codes_api.delete("/device-codes/{device_code}")
async def delete_device_code(
    device_code: str,
    device_code_service: Annotated[DeviceCodeService, Depends(DeviceCodeService)],
) -> bool:
    """Delete a device code."""
    try:
        device_code_service.delete_record_by_id(device_code)
    except Exception:
        return False
    return True
