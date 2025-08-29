"""Type definitions for versioning identifiers."""

from __future__ import annotations

from typing import NewType

VersionId = NewType("VersionId", str)
"""Unique identifier for a specific version."""

VersionRef = NewType("VersionRef", str)
"""Reference to a version (can be tag, hash, or semantic version)."""
