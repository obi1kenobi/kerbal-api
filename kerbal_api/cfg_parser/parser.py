import string
from typing import List, Optional, Set, Tuple

from .constants import comment_sequence
from .typedefs import CfgKey, ParsedCfgFile


# TODO: use a proper parsing library to create a "real" parser,
#       instead of this hacked-together monstrosity.


def parse_cfg_file(file_path: str,) -> Optional[ParsedCfgFile]:
    with open(file_path, "r") as f:
        lines: List[str] = [raw_line.strip() for raw_line in f]

    if not lines:
        return None

    visited_sections: Set[CfgKey] = set()
    current_section: List[Tuple[str, int]] = []
    data: ParsedCfgFile = {}

    if lines[0] and lines[0][0] == "\ufeff":
        # Remove byte-order marks at the start of the file
        lines[0] = lines[0][1:]

    expected_section_name_chars = set(string.ascii_letters) | set(string.digits) | {"_", "-"}
    section_like_exceptions = {
        # One of the built-in KSP files has the below string appear within a section,
        # bare (without a "= value" suffix), and without starting a new section by that name.
        # Until we figure out what this means semantically, just pretend it doesn't exist.
        "fxOriginalOffset",
    }

    for line_index, line in enumerate(lines):
        if line == "":
            continue
        elif line.startswith(comment_sequence):
            # Comment line, ignore.
            continue
        if "=" in line:
            components = [component.strip() for component in line.split("=", 1)]
            key, value = components

            counter = 0
            current_field_key = (key, counter)
            full_key = tuple(current_section) + (current_field_key,)
            while full_key in data:
                counter += 1
                current_field_key = (key, counter)
                full_key = tuple(current_section) + (current_field_key,)

            data[full_key] = value
        elif line == "{":
            continue
        elif line.startswith("}"):
            current_section.pop()
            while line != "}":
                line = line.split("}", 1)[1].strip()
                if line.startswith("}"):
                    current_section.pop()
        elif line in section_like_exceptions:
            # Certain strings appear in section-like form (unary, not key = value),
            # and we know to ignore them.
            continue
        else:
            if line.endswith("{"):
                line = line.strip("{").strip()
            else:
                next_nonempty_line_index = line_index + 1
                line_count = len(lines)
                while next_nonempty_line_index < line_count:
                    if lines[next_nonempty_line_index] == "{":
                        break
                    elif lines[next_nonempty_line_index] == "":
                        next_nonempty_line_index += 1
                        continue
                    else:
                        raise AssertionError(
                            f"Unexpected line {line_index} in file {file_path}: {line}"
                        )

                peek_next_line = (
                    lines[next_nonempty_line_index] if next_nonempty_line_index < line_count else ""
                )
                if peek_next_line != "{":
                    raise AssertionError(
                        f"Unexpected line {line_index} in file {file_path}: {line}"
                    )

            section_name = line
            if "//" in section_name:
                section_name = section_name.split("//", 1)[0].strip()

            unexpected_chars = set(section_name) - expected_section_name_chars
            if unexpected_chars:
                raise AssertionError(
                    f"Unexpected section name at line {line_index} in file {file_path}: "
                    f"{section_name}"
                )

            counter = 0

            section_key = (section_name, counter)
            fully_qualified_section_name: Tuple[Tuple[str, int], ...] = (
                tuple(current_section) + tuple(section_key,)
            )
            while fully_qualified_section_name in visited_sections:
                counter += 1
                section_key = (section_name, counter)
                fully_qualified_section_name = tuple(current_section) + tuple(section_key,)

            visited_sections.add(fully_qualified_section_name)
            current_section.append(section_key)

    return data
