"""Version table model"""

from sqlmodel import Field, Relationship

from lilypad.server.models import BaseSQLModel, FnParamsTable, LLMFunctionTable

from .table_names import FN_PARAMS_TABLE_NAME, LLM_FN_TABLE_NAME, VERSION_TABLE_NAME


class VersionBase(BaseSQLModel):
    """Version base model"""

    llm_function_id: int = Field(foreign_key=f"{LLM_FN_TABLE_NAME}.id")
    fn_params_id: int | None = Field(foreign_key=f"{FN_PARAMS_TABLE_NAME}.id")
    version: int
    function_name: str = Field(nullable=False, index=True)
    llm_function_hash: str = Field(nullable=False, index=True)
    fn_params_hash: str | None = Field(default=None, index=True)
    is_active: bool = Field(default=False)


class VersionTable(VersionBase, table=True):
    """Version table"""

    __tablename__ = VERSION_TABLE_NAME  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    llm_fn: "LLMFunctionTable" = Relationship(back_populates="version")
    fn_params: "FnParamsTable" = Relationship(back_populates="version")
