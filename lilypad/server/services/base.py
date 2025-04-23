"""The `BaseService` class from which all services inherit."""

from collections.abc import Sequence
from typing import Annotated, Any, Generic, TypeVar
from uuid import UUID

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from .._utils import get_current_user
from ..db import get_session
from ..models import BaseSQLModel
from ..schemas.users import UserPublic

_TableT = TypeVar("_TableT", bound=BaseSQLModel)
_CreateT = TypeVar("_CreateT", bound=BaseModel)


class BaseService(Generic[_TableT, _CreateT]):
    """Base class for all services."""

    table: type[_TableT]
    create_model: type[_CreateT]

    def find_record(self, **filters: Any) -> _TableT | None:
        """Find record by filters"""
        filter_conditions = [
            getattr(self.table, key) == value for key, value in filters.items()
        ]
        record_table = self.session.exec(
            select(self.table).where(
                *filter_conditions,
            )
        ).first()
        return record_table

    def find_record_by_uuid(self, uuid: UUID, **filters: Any) -> _TableT:
        """Find record by uuid"""
        record_table = self.find_record(
            uuid=uuid,
            **filters,
        )
        if not record_table:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Record for {self.table.__tablename__} not found",
            )
        return record_table

    def find_records_by_uuids(
        self, uuids: set[UUID], **filters: Any
    ) -> Sequence[_TableT]:
        """Find multiple records by their UUIDs in a single query.

        Args:
            uuids: Set of UUIDs to fetch
            filters: Additional filters to apply to the query.

        Returns:
            A sequence of records matching the UUIDs.
        """
        if not uuids:
            return []
        filter_conditions = [
            getattr(self.table, key) == value for key, value in filters.items()
        ]
        records = self.session.exec(
            select(self.table).where(self.table.uuid.in_(uuids), *filter_conditions)  # type: ignore
        ).all()

        return records

    def find_all_records(self, **filters: Any) -> Sequence[_TableT]:
        """Find all records"""
        filter_conditions = [
            getattr(self.table, key) == value for key, value in filters.items()
        ]
        res = self.session.exec(
            select(self.table).where(
                *filter_conditions,
            )
        ).all()
        return res

    def delete_record_by_uuid(self, uuid: UUID, **filters: Any) -> bool:
        """Delete record by uuid"""
        record_table = self.find_record_by_uuid(uuid, **filters)
        try:
            self.session.delete(record_table)
        except Exception:
            return False
        return True

    def create_record(self, data: _CreateT, **kwargs: Any) -> _TableT:
        """Create a new record"""
        record_table = self.table.model_validate(
            {
                **data.model_dump(),
                **kwargs,
            }
        )
        self.session.add(record_table)
        self.session.flush()
        return record_table

    def update_record_by_uuid(self, uuid: UUID, data: dict, **filters: Any) -> _TableT:
        """Updates a record based on the uuid"""
        record_table = self.find_record_by_uuid(uuid, **filters)
        record_table.sqlmodel_update(data)
        self.session.add(record_table)
        self.session.flush()
        return record_table

    def __init__(
        self,
        session: Annotated[Session, Depends(get_session)],
        user: Annotated[UserPublic, Depends(get_current_user)],
    ) -> None:
        self.session = session
        self.user = user
