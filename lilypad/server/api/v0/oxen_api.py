"""The `/oxen` API router."""

# from typing import Annotated, Sequence

# import fsspec
from fastapi import APIRouter, Depends

# from oxen import DataFrame, RemoteRepo, Workspace

# from ..._utils import get_current_user
# from ...models import AnnotationPublic, UserPublic

oxen_router = APIRouter()


# def get_repo() -> RemoteRepo:
#     active_organization_uuid = "a033e136-eaab-43d4-aee3-dbea8efac706"
#     repo = RemoteRepo(f"bkao/{active_organization_uuid}")
#     if not repo.exists():
#         repo.create()
#     return repo


# @oxen_router.post("/projects/{project_uuid}/oxen")
# async def create_dataset(repo: Annotated[RemoteRepo, Depends(get_repo)]) -> bool:
#     # repo.add("data.csv", dst_dir="generations/generationUuid")
#     # repo.commit("initial commit")
#     # workspace = Workspace(repo, "main", workspace_id="123")
#     try:
#         data_frame = DataFrame(repo, "data.csv")
#     except ValueError:
#         repo.add("data.csv")
#         repo.commit("initial commit")

#     data_frame = DataFrame(repo, "data.csv")
#     data_frame.insert_row({"category": "not spam", "message": "..."})
#     data_frame.commit("commit data frame.")

#     # row_id = data_frame.insert_row({"category": "not spam", "message": "..."})
#     # workspace.commit("commit workspace.")
#     return True


# @oxen_router.get("/projects/{project_uuid}/generations/{generation_uuid}/oxen")
# async def get_dataset(
#     repo: Annotated[RemoteRepo, Depends(get_repo)],
# ) -> Sequence[AnnotationPublic]:
#     data_frame = DataFrame(repo, "data.csv")
#     res = data_frame.query()
#     print(res)
#     return []
