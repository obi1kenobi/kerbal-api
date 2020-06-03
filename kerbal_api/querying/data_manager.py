from os import path
from typing import Dict, List, Type, TypeVar

from ..cfg_parser.file_finder import get_ksp_part_cfg_files
from ..cfg_parser.parser import load_part_config_from_cfg_file
from ..cfg_parser.typedefs import ParsedCfgFile
from .tokens import KerbalToken, make_part_token


def _canonicalize_path(file_path: str) -> str:
    # Expand symbolic links, then normalize the path and its case, and convert to an absolute path.
    # We expand symbolic links before normalizing, because those operations do not commute:
    # https://docs.python.org/3/library/os.path.html#os.path.normpath
    real_path = path.realpath(file_path)
    normalized_path = path.normcase(path.normpath(real_path))
    return path.abspath(normalized_path)


K = TypeVar("K")
V = TypeVar("V")


def _set_without_overwriting(mapping: Dict[K, V], new_key: K, new_value: V) -> None:
    if new_key in mapping:
        raise AssertionError(
            f"Setting {new_key}={new_value} would have unexpectedly overwritten "
            f"an existing value: {mapping[new_key]}"
        )

    mapping[new_key] = new_value


T = TypeVar("T", bound="KerbalDataManager")


class KerbalDataManager:
    parsed_cfg_files: Dict[str, ParsedCfgFile]  # mapping file path to parsed data

    # Part data management
    parts: List[KerbalToken]  # authoritative list of all known parts
    parts_by_cfg_file_path: Dict[
        str, KerbalToken
    ]  # index of parts by origin config file path
    parts_by_name: Dict[
        str, List[KerbalToken]
    ]  # index of parts by display name, not unique
    parts_by_internal_name: Dict[
        str, List[KerbalToken]
    ]  # index of parts by internal name, not unique
    # End part data management

    def __init__(self) -> None:
        self.parsed_cfg_files = {}

        self.parts = []
        self.parts_by_cfg_file_path = {}
        self.parts_by_name = {}
        self.parts_by_internal_name = {}

    @classmethod
    def from_ksp_install_path(cls: Type[T], ksp_install_path: str) -> T:
        result = cls()

        for cfg_file in get_ksp_part_cfg_files(ksp_install_path):
            result.ingest_cfg_file(cfg_file)

        return result

    def ingest_cfg_file(self, file_path: str) -> None:
        canonicalized_path = _canonicalize_path(file_path)
        if canonicalized_path in self.parsed_cfg_files:
            # All done, this is a no-op.
            return

        cfg_file = load_part_config_from_cfg_file(canonicalized_path)
        if cfg_file is None:
            # This is not a cfg file format we recognize. Nothing to be done.
            return

        part_token = make_part_token(canonicalized_path, cfg_file)
        if part_token is not None:
            part_name = part_token.content["name"]
            part_internal_name = part_token.content["internal_name"]

            self.parts.append(part_token)
            _set_without_overwriting(
                self.parts_by_cfg_file_path, canonicalized_path, part_token
            )
            self.parts_by_internal_name.setdefault(part_internal_name, []).append(
                part_token
            )
            self.parts_by_name.setdefault(part_name, []).append(part_token)
