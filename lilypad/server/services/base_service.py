"""BaseService class for all services"""

from collections.abc import Sequence
from typing import Annotated, Any, Generic, TypeVar

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from lilypad.server.db import get_session
from lilypad.server.models import BaseSQLModel

T = TypeVar("T", bound=BaseSQLModel)
CreateT = TypeVar("CreateT", bound=BaseModel)


class BaseService(Generic[T, CreateT]):
    """BaseService class for all services"""

    table: type[T]
    create_model: type[CreateT]

    def find_record_by_id(self, id: int | str) -> T:
        """Find record by id"""
        record_table = self.session.exec(
            select(self.table).where(
                self.table.id == id,  # pyright: ignore[reportAttributeAccessIssue]
            )
        ).first()
        if not record_table:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Record for {self.table.__tablename__} not found",
            )
        return record_table

    def find_all_records(self) -> Sequence[T]:
        """Find all records"""
        return self.session.exec(select(self.table)).all()

    def delete_record_by_id(self, id: int | str) -> None:
        """Delete record by uuid"""
        record_table = self.find_record_by_id(id)
        self.session.delete(record_table)
        return

    def create_record(self, data: CreateT, **kwargs: Any) -> T:
        """Create a new record"""
        record_table = self.table.model_validate({**data.model_dump(), **kwargs})
        self.session.add(record_table)
        self.session.flush()
        return record_table

    def update_record_by_id(self, id: int | str, data: dict) -> T:
        """Updates a record based on the id"""
        record_table = self.find_record_by_id(id)
        record_table.sqlmodel_update(data)
        self.session.add(record_table)
        self.session.flush()
        return record_table

    def __init__(
        self,
        session: Annotated[Session, Depends(get_session)],
    ) -> None:
        self.session = session
