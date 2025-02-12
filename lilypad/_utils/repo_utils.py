from __future__ import annotations

from oxen import RemoteRepo


def create_repo_if_not_exists(
    repo: RemoteRepo,
    is_public: bool = False,
    empty: bool = False,
) -> RemoteRepo:
    """Create the repository if it does not already exist.

    Args:
        repo: The RemoteRepo object.
        is_public: Whether the repository is public (default: False).
        empty: Whether to create an empty repository (default: False).

    Returns:
        The RemoteRepo object (created if it did not exist).
    """
    if not repo.exists():
        repo.create(empty=empty, is_public=is_public)
    return repo


def change_repo_branch(
    repo: RemoteRepo,
    new_branch: str,
    create: bool = False,
) -> None:
    """Change the branch of the repository.

    If the specified branch does not exist and `create` is True, the branch
    will be created.

    Args:
        repo: The RemoteRepo object.
        new_branch: The branch name to switch to.
        create: Whether to create the branch if it does not exist (default: False).
    """
    repo.checkout(new_branch, create=create)


def create_new_repo(
    name: str,
    is_public: bool = True,
    host: str = "hub.oxen.ai",
    scheme: str = "https",
) -> RemoteRepo:
    """Create a new remote repository using the Oxen backend.

    Args:
        name: Repository name in the format "namespace/repo_name".
        is_public: Whether the repository is public (default: True).
        host: The host to connect to (default: "hub.oxen.ai").
        scheme: The scheme to use (default: "https").

    Returns:
        The created RemoteRepo object.
    """
    repo = RemoteRepo(name, host=host, revision="main", scheme=scheme)
    repo.create(empty=False, is_public=is_public)
    return repo
