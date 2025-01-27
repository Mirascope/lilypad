"""The `/oxen` API router."""

from typing import Annotated, Sequence

from fastapi import APIRouter, Depends
from oxen import DataFrame, RemoteRepo, Workspace

from ..._utils import get_current_user
from ...models import AnnotationPublic, UserPublic

oxen_router = APIRouter()


def get_repo() -> RemoteRepo:
    active_organization_uuid = "a033e136-eaab-43d4-aee3-dbea8efac706"
    repo = RemoteRepo(f"bkao/{active_organization_uuid}")
    if not repo.exists():
        repo.create()
    return repo


@oxen_router.post("/projects/{project_uuid}/oxen")
async def create_dataset(repo: Annotated[RemoteRepo, Depends(get_repo)]) -> bool:
    data_frame = DataFrame("bkao/{active_organization_uuid}", "data.csv")
    row_id = data_frame.insert_row({"category": "not spam", "message": "Github PR"})
    row = data_frame.get_row_by_id(row_id)

    return True


@oxen_router.get("/projects/{project_uuid}/generations/{generation_uuid}/oxen")
async def get_dataset(
    repo: Annotated[RemoteRepo, Depends(get_repo)],
) -> Sequence[AnnotationPublic]:
    data_frame = DataFrame(repo, "data.csv")
    res = data_frame.query()
    print(res)
    return []
