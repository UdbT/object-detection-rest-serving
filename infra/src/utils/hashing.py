"""Hashing utilities for CDK bundling.

To support Poetry path dependencies, the project root is used as a bundling root.
By default, CDK uses bundling root for calculating asset hash. This would trigger
re-bundling on any change. Use custom hashing strategy to include only relevant
content for hashing.

Note: fetch the code from sertis-de-toolkit repository (sertis_de_toolkit.core/sertis_de_toolkit/core/hashing.py)
"""

import hashlib
from pathlib import Path


def new_hash() -> hashlib.blake2b:
    """Creates a new hash.

    This wraps `hashlib` hash creation in case the hash algorithm will be changed in the future.

    Returns:
        A hashlib hash
    """
    return hashlib.blake2b(digest_size=32)


def calculate_hash(*paths: Path) -> str:
    """Calculate a hash for paths.

    Args:
        *paths: Paths to hash

    Returns:
        A hash digest string
    """
    file_hash = new_hash()

    def handle_path(path: Path) -> None:
        file_hash.update(str(path).encode("utf-8"))
        if path.is_file():
            with path.open("rb") as file:
                while chunk := file.read(8192):
                    file_hash.update(chunk)
        else:
            for child in sorted(path.rglob("*")):
                handle_path(child)

    for path in paths:
        handle_path(path)

    return file_hash.hexdigest()
