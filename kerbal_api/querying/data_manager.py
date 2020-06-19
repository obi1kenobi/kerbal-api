from os import path
from typing import Dict, List, Type, TypeVar

from ..cfg_parser.coercing_reads import read_bool, read_float, read_raw, read_str
from ..cfg_parser.file_finder import get_ksp_part_cfg_files
from ..cfg_parser.parser import parse_cfg_file
from ..cfg_parser.typedefs import CfgKey, ParsedCfgFile
from .tokens import KerbalConfigToken, make_part_token, make_resource_tokens


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
    parts: List[KerbalConfigToken]  # authoritative list of all known parts
    parts_by_cfg_file_path: Dict[
        str, KerbalConfigToken
    ]  # index of parts by origin config file path
    parts_by_name: Dict[str, List[KerbalConfigToken]]  # index of parts by display name, not unique
    parts_by_internal_name: Dict[
        str, List[KerbalConfigToken]
    ]  # index of parts by internal name, not unique

    resources: List[KerbalConfigToken]  # authoritative list of all known resources
    resources_by_name: Dict[str, KerbalConfigToken]  # index of resources by display name
    resources_by_internal_name: Dict[str, KerbalConfigToken]  # index of resources by internal name
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

        cfg_file = parse_cfg_file(canonicalized_path)
        if cfg_file is None:
            # This is not a cfg file format we recognize. Nothing to be done.
            return

        self.parsed_cfg_files[canonicalized_path] = cfg_file

        part_token = make_part_token(canonicalized_path, cfg_file)
        if part_token is not None:
            part_name = part_token.content["name"]
            part_internal_name = part_token.content["internal_name"]

            self.parts.append(part_token)
            _set_without_overwriting(self.parts_by_cfg_file_path, canonicalized_path, part_token)
            self.parts_by_internal_name.setdefault(part_internal_name, []).append(part_token)
            self.parts_by_name.setdefault(part_name, []).append(part_token)

        resource_tokens = make_resource_tokens(canonicalized_path, cfg_file)
        for resource_token in resource_tokens:
            resource_name = resource_token.content["name"]
            resource_internal_name = resource_token.content["internal_name"]

            self.resources.append(resource_token)
            _set_without_overwriting(self.resources_by_name, resource_name, resource_token)
            _set_without_overwriting(
                self.resources_by_internal_name, resource_internal_name, resource_token
            )


def _make_engine_module_token(
    data_manager: KerbalDataManager, cfg_file_path: str, cfg_path_root: CfgKey,
) -> KerbalConfigToken:
    parsed_cfg_file = data_manager.parsed_cfg_files[cfg_file_path]
    type_name = "EngineModule"

    content: Dict[str, Any] = {}
    content["min_thrust"] = read_float(parsed_cfg_file, cfg_path_root + (("minThrust", 0),))
    content["max_thrust"] = read_float(parsed_cfg_file, cfg_path_root + (("maxThrust", 0),))
    content["throttleable"] = not read_bool(
        parsed_cfg_file, cfg_path_root + (("throttleLocked", 0),), default=False
    )

    atmosphere_curve: Dict[float, float] = {}
    curve_root_key = cfg_path_root + (("atmosphereCurve", 0),)

    counter = 0
    curve_step_key = curve_root_key + (("key", counter),)
    while curve_step_key in parsed_cfg_file:
        data = read_raw(parsed_cfg_file, curve_step_key)
        assert data is not None

        components = data.split(" ")
        assert len(components) >= 2, components

        atmosphere_coefficient = float(components[0])
        isp = float(components[1])
        atmosphere_curve[atmosphere_coefficient] = isp

        counter += 1
        curve_step_key = curve_root_key + (("key", counter),)

    content["isp_vacuum"] = atmosphere_curve.get(0.0, None)
    content["isp_at_1atm"] = atmosphere_curve.get(1.0, None)

    return KerbalConfigToken(type_name, content, cfg_file_path, cfg_path_root)


def get_engine_modules_for_part(
    data_manager: KerbalDataManager, token: KerbalConfigToken
) -> List[KerbalConfigToken]:
    assert token.type_name == "Part"

    results: List[KerbalConfigToken] = []

    parsed_cfg_file = data_manager.parsed_cfg_files[token.from_cfg_file_path]

    cfg_key_base = token.from_cfg_root
    counter = 0

    cfg_key = cfg_key_base + (("MODULE", counter),)
    module_name_key = cfg_key + (("name", 0),)

    while module_name_key in parsed_cfg_file:
        if parsed_cfg_file.get(module_name_key, "") in {"ModuleEngines", "ModuleEnginesFX"}:
            results.append(
                _make_engine_module_token(data_manager, token.from_cfg_file_path, cfg_key)
            )

        counter += 1
        cfg_key = cfg_key_base + (("MODULE", counter),)
        module_name_key = cfg_key + (("name", 0),)

    return results


def _make_contained_resource_token(
    data_manager: KerbalDataManager, cfg_file_path: str, cfg_path_root: CfgKey,
) -> KerbalConfigToken:
    parsed_cfg_file = data_manager.parsed_cfg_files[cfg_file_path]
    type_name = "ContainedResource"

    content: Dict[str, Any] = {}
    content["resource_internal_name"] = read_str(parsed_cfg_file, cfg_path_root + (("name", 0),))
    content["amount"] = read_float(parsed_cfg_file, cfg_path_root + (("amount", 0),))
    content["max_amount"] = read_float(parsed_cfg_file, cfg_path_root + (("maxAmount", 0),))

    return KerbalConfigToken(type_name, content, cfg_file_path, cfg_path_root)


def get_default_resources_for_part(
    data_manager: KerbalDataManager, token: KerbalConfigToken,
) -> List[KerbalConfigToken]:
    assert token.type_name == "Part"

    results: List[KerbalConfigToken] = []

    parsed_cfg_file = data_manager.parsed_cfg_files[token.from_cfg_file_path]

    cfg_key_base = token.from_cfg_root
    counter = 0

    cfg_key = cfg_key_base + (("RESOURCE", counter),)
    resource_name_key = cfg_key + (("name", 0),)

    while resource_name_key in parsed_cfg_file:
        results.append(
            _make_contained_resource_token(data_manager, token.from_cfg_file_path, cfg_key)
        )

        counter += 1
        cfg_key = cfg_key_base + (("RESOURCE", counter),)
        resource_name_key = cfg_key + (("name", 0),)

    return results
