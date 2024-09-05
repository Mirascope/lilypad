"""Main FastAPI application module for Lilypad."""

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request) -> HTMLResponse:
    """Render the index.html template."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/submit", response_class=HTMLResponse)
async def submit(request: Request, input_value: str = Form(...)) -> HTMLResponse:
    """Render the result.html template."""
    return templates.TemplateResponse(
        "partials/result.html", {"request": request, "input_value": input_value}
    )
