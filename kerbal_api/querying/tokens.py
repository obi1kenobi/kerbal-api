from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

from ..cfg_parser.coercing_reads import read_bool, read_float, read_int, read_str
from ..cfg_parser.typedefs import CfgKey, ParsedCfgFile


@dataclass
class KerbalToken:
    type_name: str
    content: Dict[str, Any]  # field values
    foreign_keys: Dict[str, Any]  # values that help us look up neighbors


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

    return KerbalConfigToken(type_name, content, {}, cfg_file_path, base_key)


def make_resource_tokens(
    cfg_file_path: str, parsed_cfg_file: ParsedCfgFile
) -> List[KerbalConfigToken]:
    type_name = "Resource"

    results: List[KerbalConfigToken] = []

    counter = 0
    base_key = (("RESOURCE_DEFINITION", counter),)
    name_key = base_key + (("name", 0),)

    while name_key in parsed_cfg_file:
        content: Dict[str, Any] = {
            "cfg_file_path": cfg_file_path,
            "internal_name": read_str(parsed_cfg_file, name_key),
            "name": read_str(parsed_cfg_file, base_key + (("displayName", 0),)),
            "density": read_float(parsed_cfg_file, base_key + (("density", 0),)),
            "specific_heat": read_float(parsed_cfg_file, base_key + (("hsp", 0),)),
            "unit_cost": read_float(parsed_cfg_file, base_key + (("unitCost", 0),)),
            "specific_volume": read_float(
                parsed_cfg_file, base_key + (("volume", 0),), default=0.0,
            ),
        }

        results.append(KerbalConfigToken(type_name, content, {}, cfg_file_path, base_key))

        counter += 1
        base_key = (("RESOURCE_DEFINITION", counter),)
        name_key = base_key + (("name", 0),)

    return results


def make_technology_tokens(
    cfg_file_path: str, parsed_cfg_file: ParsedCfgFile
) -> List[KerbalConfigToken]:
    type_name = "Technology"

    results: List[KerbalConfigToken] = []

    counter = 0
    base_key = (("TechTree", 0), ("RDNode", counter))
    id_key = base_key + (("id", 0),)

    while id_key in parsed_cfg_file:
        content: Dict[str, Any] = {
            "cfg_file_path": cfg_file_path,
            "id": read_str(parsed_cfg_file, id_key),
            "name": read_str(parsed_cfg_file, base_key + (("title", 0),)),
            "description": read_str(parsed_cfg_file, base_key + (("description", 0),)),
            "science_cost": read_float(parsed_cfg_file, base_key + (("cost", 0),)),
        }

        any_of_prereqs = read_bool(parsed_cfg_file, base_key + (("anyToUnlock", 0),))
        foreign_keys: Dict[str, Any] = {
            "mandatory_prereq_ids": [],
            "any_of_prereq_ids": [],
        }

        prereq_counter = 0
        prereq_key = base_key + (("Parent", prereq_counter), ("parentID", 0))
        while prereq_key in parsed_cfg_file:
            prereq_id = read_str(parsed_cfg_file, prereq_key)
            if any_of_prereqs:
                foreign_keys["any_of_prereq_ids"].append(prereq_id)
            else:
                foreign_keys["mandatory_prereq_ids"].append(prereq_id)

            prereq_counter += 1
            prereq_key = base_key + (("Parent", prereq_counter), ("parentID", 0))

        # Fix for occasional game data problem: "any of" requirement, but only one tech.
        # We make such prerequisites mandatory, since there is no choice to be made.
        if len(foreign_keys["any_of_prereq_ids"]) == 1:
            foreign_keys["mandatory_prereq_ids"].extend(foreign_keys["any_of_prereq_ids"])
            foreign_keys["any_of_prereq_ids"] = []

        results.append(KerbalConfigToken(type_name, content, foreign_keys, cfg_file_path, base_key))

        counter += 1
        base_key = (("TechTree", 0), ("RDNode", counter))
        id_key = base_key + (("id", 0),)

    return results
