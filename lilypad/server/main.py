"""Main FastAPI application module for Lilypad."""

from typing import Annotated, Sequence

from fastapi import Depends, FastAPI, Form, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlmodel import Session, select

from lilypad.server.db.session import get_session
from lilypad.server.models import CallTable, ProjectTable, PromptVersionTable
from lilypad.server.models.calls import CallBase
from lilypad.server.models.prompt_versions import PromptVersionBase

app = FastAPI()

origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
templates = Jinja2Templates(directory="templates")
api = FastAPI()


class PromptVersionPublic(PromptVersionBase):
    """Prompt Version public model."""

    id: int


@api.get("/prompt-versions/{version_hash}")
async def get_prompt_version_id_by_hash(
    version_hash: str,
    session: Annotated[Session, Depends(get_session)],
) -> int:
    """Get prompt version id by hash."""
    prompt_version = session.exec(
        select(PromptVersionTable).where(
            PromptVersionTable.version_hash == version_hash
        )
    ).first()
    # Stainless does not handle `int | None` return types properly
    return (
        PromptVersionPublic.model_validate(prompt_version).id if prompt_version else -1
    )


@api.post(
    "/prompt-versions",
    response_model=PromptVersionPublic,
)
async def create_prompt_version(
    prompt_version_create: PromptVersionBase,
    session: Annotated[Session, Depends(get_session)],
) -> PromptVersionTable:
    """Creates a prompt version."""
    prompt_version = PromptVersionTable.model_validate(prompt_version_create)
    session.add(prompt_version)
    session.commit()
    session.refresh(prompt_version)
    return prompt_version


class CallPublicWithPromptVersion(CallBase):
    """Call public model with prompt version."""

    id: int
    prompt_version: PromptVersionPublic


@api.get("/calls", response_model=Sequence[CallPublicWithPromptVersion])
async def get_calls(
    session: Annotated[Session, Depends(get_session)],
) -> Sequence[CallPublicWithPromptVersion]:
    """Creates a logged call."""
    call_tables = session.exec(select(CallTable)).all()
    return call_tables


@api.post("/calls")
async def create_calls(
    session: Annotated[Session, Depends(get_session)], call_create: CallBase
) -> CallTable:
    """Creates a logged call."""
    call = CallTable.model_validate(call_create)
    session.add(call)
    session.commit()
    session.refresh(call)
    return call


app.mount("/api", api)
