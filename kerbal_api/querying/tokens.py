from dataclasses import dataclass
from typing import Any, Dict, Optional, Set

from ..cfg_parser.coercing_reads import read_float, read_int, read_str
from ..cfg_parser.parser import load_part_config_from_cfg_file


@dataclass
class KerbalToken:
    type_name: str
    content: Dict[str, Any]


def make_part_token(file_path: str) -> Optional[KerbalToken]:
    part_config = load_part_config_from_cfg_file(file_path)
    if part_config is None:
        return None

    type_name = "Part"

    base_key = (("PART", 0),)

    internal_name = read_str(part_config, base_key + (("name", 0),))

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
        "cfg_file_path": file_path,
        "internal_name": internal_name,
        "name": read_str(part_config, base_key + (("title", 0),)),
        "manufacturer": read_str(
            part_config, base_key + (("manufacturer", 0),), default="N/A"
        ),
        "cost": read_int(part_config, base_key + (("cost", 0),)),
        "dry_mass": read_float(part_config, base_key + (("mass", 0),)),
        "crash_tolerance": read_float(part_config, base_key + (("crashTolerance", 0),)),
        "max_temp_tolerance": read_float(
            part_config, base_key + (("maxTemp", 0),), default=1200.0
        ),
    }

    return KerbalToken(type_name, content)
