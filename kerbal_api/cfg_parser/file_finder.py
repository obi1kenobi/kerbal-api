from glob import iglob
import os
from typing import Iterable


def get_cfg_files_recursively(glob_path: str) -> Iterable[str]:
    """Get all *.cfg file paths recursively starting at a given path, supporting glob rules."""
    glob_search_path = os.path.join(glob_path, "**", "*.cfg")
    return iglob(glob_search_path, recursive=True)


def get_ksp_part_cfg_files(ksp_install_path: str) -> Iterable[str]:
    """Get *.cfg file paths whose location suggests they are categorized as Parts."""
    glob_search_path = os.path.join(ksp_install_path, "GameData", "**", "Parts")
    return get_cfg_files_recursively(glob_search_path)
