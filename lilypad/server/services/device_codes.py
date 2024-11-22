"""The `DeviceCodeService` class for device_codes."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlmodel import Session, select

from ..db import get_session
from ..models import DeviceCodeTable


class DeviceCodeService:
    """The service class for device_codes."""

    table: type[DeviceCodeTable] = DeviceCodeTable

    def find_record_by_id(self, id: str) -> DeviceCodeTable:
        """Find DeviceCode by id"""
        record_table = self.session.exec(
            select(self.table).where(self.table.id == id)
        ).first()
        if not record_table:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Record for {self.table.__tablename__} not found",
            )
        return record_table

    def delete_record_by_id(self, id: str) -> None:
        """Delete DeviceCode record by id"""
        record_table = self.find_record_by_id(id)
        self.session.delete(record_table)
        return

    def create_record(self, device_code: str, token: str) -> DeviceCodeTable:
        """Create a new DeviceCode record"""
        record_table = self.table(id=device_code, token=token)
        self.session.add(record_table)
        self.session.flush()
        return record_table

    def __init__(
        self,
        session: Annotated[Session, Depends(get_session)],
    ) -> None:
        self.session = session
