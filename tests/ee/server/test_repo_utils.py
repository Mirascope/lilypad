"""Tests for the repository utility functions."""

from __future__ import annotations

from unittest.mock import MagicMock

from lilypad.ee.server import repo_utils


def test_create_repo_if_not_exists_when_repo_does_not_exist() -> None:
    """Test that create_repo_if_not_exists creates the repository if it does not exist."""
    mock_repo = MagicMock()
    mock_repo.exists.return_value = False
    repo_utils.create_repo_if_not_exists(mock_repo, is_public=False, empty=False)
    mock_repo.create.assert_called_once_with(empty=False, is_public=False)


def test_create_repo_if_not_exists_when_repo_exists() -> None:
    """Test that create_repo_if_not_exists does not create the repository if it already exists."""
    mock_repo = MagicMock()
    mock_repo.exists.return_value = True
    repo_utils.create_repo_if_not_exists(mock_repo, is_public=False, empty=False)
    mock_repo.create.assert_not_called()


def test_change_repo_branch() -> None:
    """Test that change_repo_branch changes the branch of the repository."""
    mock_repo = MagicMock()
    new_branch = "feature/new-branch"
    repo_utils.change_repo_branch(mock_repo, new_branch, create=True)
    mock_repo.checkout.assert_called_once_with(new_branch, create=True)


def test_create_new_repo(monkeypatch) -> None:
    """Test that create_new_repo creates a new repository."""

    # Create a dummy RemoteRepo class to simulate the behavior.
    class DummyRemoteRepo:
        def __init__(self, name: str, host: str, revision: str, scheme: str) -> None:
            self.name = name
            self.host = host
            self.revision = revision
            self.scheme = scheme
            self.created = False

        def create(self, empty: bool, is_public: bool) -> None:
            self.created = True

        def exists(self) -> bool:
            return False

    monkeypatch.setattr(repo_utils, "RemoteRepo", DummyRemoteRepo)
    repo = repo_utils.create_new_repo(
        "namespace/repo_name", is_public=False, host="hub.oxen.ai", scheme="https"
    )
    assert isinstance(repo, DummyRemoteRepo)
    assert repo.created is True
