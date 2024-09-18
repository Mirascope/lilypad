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


class CallCreate(BaseModel):
    """Call create model."""

    project_name: str
    input: str
    output: str


class PromptVersionPublic(PromptVersionBase):
    """Prompt Version public model."""

    id: int


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
    session: Annotated[Session, Depends(get_session)], call_create: CallCreate
) -> bool:
    """Creates a logged call."""
    project = session.exec(
        select(ProjectTable).where(ProjectTable.name == call_create.project_name)
    ).first()

    if not project:
        raise HTTPException(status_code=404)

    prompt_version = sorted(
        project.prompt_versions, key=lambda x: x.id or 0, reverse=True
    )[:1][0]

    if not prompt_version or not prompt_version.id:
        raise HTTPException(status_code=404)

    call = CallTable(
        prompt_version_id=prompt_version.id,
        input=call_create.input,
        output=call_create.output,
    )
    session.add(call)
    session.commit()
    session.flush()
    return True


app.mount("/api", api)
