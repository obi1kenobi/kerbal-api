from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

from ..cfg_parser.coercing_reads import read_float, read_int, read_str
from ..cfg_parser.typedefs import CfgKey, ParsedCfgFile


@dataclass
class KerbalToken:
    type_name: str
    content: Dict[str, Any]


@dataclass
class KerbalConfigToken(KerbalToken):
    from_cfg_file_path: str
    from_cfg_root: CfgKey


def make_part_token(cfg_file_path: str, part_config: ParsedCfgFile) -> Optional[KerbalConfigToken]:
    type_name = "Part"

    base_key = (("PART", 0),)
    name_key = base_key + (("name", 0),)

    if name_key not in part_config:
        # There is no part definition in this file.
        return None

    internal_name = read_str(part_config, name_key)

    non_part_blacklist: Set[str] = {
        "flag",
        "kerbalEVA",
        "kerbalEVAFuture",
        "kerbalEVAVintage",
        "kerbalEVAfemale",
        "kerbalEVAfemaleFuture",
        "kerbalEVAfemaleVintage",
    }
    if internal_name in non_part_blacklist:
        return None

    content: Dict[str, Any] = {
        "cfg_file_path": cfg_file_path,
        "internal_name": internal_name,
        "name": read_str(part_config, base_key + (("title", 0),)),
        "manufacturer": read_str(part_config, base_key + (("manufacturer", 0),), default="N/A"),
        "cost": read_int(part_config, base_key + (("cost", 0),)),
        "dry_mass": read_float(part_config, base_key + (("mass", 0),)),
        "crash_tolerance": read_float(part_config, base_key + (("crashTolerance", 0),)),
        "max_temp_tolerance": read_float(part_config, base_key + (("maxTemp", 0),), default=1200.0),
    }

    return KerbalConfigToken(type_name, content, cfg_file_path, base_key)


def make_resource_tokens(cfg_file_path: str, parsed_cfg_file: ParsedCfgFile) -> List[KerbalConfigToken]:
    type_name = "Resource"

    results: List[KerbalConfigToken] = []

    counter = 0
    base_key = (("RESOURCE_DEFINITION", counter),)
    name_key = base_key + (("name", 0),)

    while name_key in parsed_cfg_file:
        content: Dict[str, Any] = {}

        content["internal_name"] = read_str(parsed_cfg_file, name_key)
        content["name"] = read_str(parsed_cfg_file, base_key + (("displayName", 0),))
        content["density"] = read_float(parsed_cfg_file, base_key + (("density", 0),))
        content["specific_heat"] = read_float(parsed_cfg_file, base_key + (("hsp", 0),))
        content["unit_cost"] = read_float(parsed_cfg_file, base_key + (("unitCost", 0),))
        content["specific_volume"] = read_float(parsed_cfg_file, base_key + (("volume", 0),))

        counter += 1
        base_key = (("RESOURCE_DEFINITION", counter),)
        name_key = base_key + (("name", 0),)

    return results
