"""Main FastAPI application module for Lilypad."""

from typing import Annotated

from fastapi import Depends, FastAPI, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from lilypad.app.db.session import get_session
from lilypad.app.models.projects import ProjectTable

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
    return RedirectResponse(url=f"/create-project/{project.name}", status_code=303)


@app.get("/create-project/{project_name}", response_class=HTMLResponse)
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
