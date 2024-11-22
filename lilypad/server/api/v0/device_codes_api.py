"""The `/device_codes` API router."""

from typing import Annotated

from fastapi import APIRouter, Depends

from ...models import DeviceCodeTable
from ...services import DeviceCodeService

device_codes_api = APIRouter()


@device_codes_api.get("/device-codes/{device_code}", response_model=DeviceCodeTable)
async def get_device_code(
    device_code: str,
    device_code_service: Annotated[DeviceCodeService, Depends(DeviceCodeService)],
) -> DeviceCodeTable:
    """Get a device code."""
    return device_code_service.find_record_by_id(device_code)


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
