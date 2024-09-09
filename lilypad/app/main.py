"""Main FastAPI application module for Lilypad."""

from typing import Annotated

from fastapi import Depends, FastAPI, Form, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlmodel import Session, select

from lilypad.app.db.session import get_session
from lilypad.app.models import CallTable, ProjectTable, PromptVersionTable

app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def projects(request: Request) -> HTMLResponse:
    """Render the projects.html template."""
    return templates.TemplateResponse("projects.html", {"request": request})


@app.get("/projects", response_class=HTMLResponse)
async def get_projects(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
) -> HTMLResponse:
    """Get all projects from the database."""
    projects = session.exec(select(ProjectTable)).all()
    return templates.TemplateResponse(
        "partials/project_list.html", {"request": request, "projects": projects}
    )


@app.post("/projects")
async def add_project(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    project_name: str = Form(...),
) -> RedirectResponse:
    """Add a project to the database."""
    project = ProjectTable(name=project_name)
    session.add(project)
    session.commit()
    session.flush()
    return RedirectResponse(url=f"/projects/{project.name}", status_code=303)


@app.get("/projects/{project_name}", response_class=HTMLResponse)
async def create_project(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    project_name: str,
) -> HTMLResponse:
    """Render the create_project.html template."""
    project = session.exec(
        select(ProjectTable).where(ProjectTable.name == project_name)
    ).first()
    return templates.TemplateResponse(
        "create_project.html", {"request": request, "project": project}
    )


@app.get("/projects/{project_name}", response_class=HTMLResponse)
async def show_project(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    project_name: str,
) -> HTMLResponse:
    """Render the create_project.html template."""
    project = session.exec(
        select(ProjectTable).where(ProjectTable.name == project_name)
    ).first()
    return templates.TemplateResponse(
        "create_project.html", {"request": request, "project": project}
    )


@app.get(
    "/projects/{project_name}/versions",
    response_model=PromptVersionTable,
)
async def get_prompt_versions(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    project_name: str,
    hx_request: str | None = Header(None),
) -> HTMLResponse | PromptVersionTable:
    """Render the version_list.html template."""
    project = session.exec(
        select(ProjectTable).where(ProjectTable.name == project_name)
    ).first()
    if not project:
        raise HTTPException(status_code=404)
    if hx_request:
        return templates.TemplateResponse(
            "partials/version_list.html",
            {
                "request": request,
                "project": project,
                "prompt_versions": project.prompt_versions,
            },
        )
    else:
        return sorted(project.prompt_versions, key=lambda x: x.id or 0, reverse=True)[
            :1
        ][0]


@app.post("/projects/{project_name}/versions")
async def create_version(
    session: Annotated[Session, Depends(get_session)],
    project_name: str,
    prompt_template: str = Form(...),
) -> RedirectResponse:
    """Render the create_version.html template."""
    project = session.exec(
        select(ProjectTable).where(ProjectTable.name == project_name)
    ).first()

    if not project or not project.id:
        raise HTTPException(status_code=404)

    latest_prompt_version = session.exec(
        select(PromptVersionTable).order_by("id")
    ).first()

    prompt_version = PromptVersionTable(
        project_id=project.id,
        prompt_template=prompt_template,
        previous_version_id=latest_prompt_version.id if latest_prompt_version else None,
    )
    session.add(prompt_version)
    session.commit()
    session.flush()
    return RedirectResponse(
        url=f"/projects/{project_name}/versions/{prompt_version.id}", status_code=303
    )


@app.get(
    "/projects/{project_name}/versions/{prompt_version_id}", response_class=HTMLResponse
)
async def view_version(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    project_name: str,
    prompt_version_id: str,
) -> HTMLResponse:
    """Render the create_version.html template."""
    prompt_version = session.exec(
        select(PromptVersionTable).where(PromptVersionTable.id == prompt_version_id)
    ).first()

    if not prompt_version:
        raise HTTPException(status_code=404)

    return templates.TemplateResponse(
        "create_project.html",
        {
            "request": request,
            "prompt_template": prompt_version.prompt_template,
            "project": prompt_version.project,
        },
    )


class CallCreate(BaseModel):
    """Call create model."""

    project_name: str
    input: str
    output: str


@app.post("/calls")
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
