from typing import Any, Dict, Optional, Tuple

from .constants import comment_sequence, localization_pattern


def read_raw(
    config_data: Dict[Tuple[Tuple[str, int], ...], Any],
    path: Tuple[Tuple[str, int], ...],
) -> Optional[str]:
    raw_value = config_data.get(path, None)
    if raw_value is None:
        return None

    if comment_sequence in raw_value:
        raw_value = raw_value.split(comment_sequence, 1)[0]

    return raw_value


def read_float(
    config_data: Dict[Tuple[Tuple[str, int], ...], Any],
    path: Tuple[Tuple[str, int], ...],
    *,
    default: Optional[float] = None,
) -> float:
    raw_value = read_raw(config_data, path)
    if raw_value is None:
        if default is None:
            raise KeyError(path)
        else:
            return default

    return float(raw_value)


def read_int(
    config_data: Dict[Tuple[Tuple[str, int], ...], Any],
    path: Tuple[Tuple[str, int], ...],
    *,
    default: Optional[int] = None,
) -> int:
    raw_value = read_raw(config_data, path)
    if raw_value is None:
        if default is None:
            raise KeyError(path)
        else:
            return default

    return int(raw_value)


def read_bool(
    config_data: Dict[Tuple[Tuple[str, int], ...], Any],
    path: Tuple[Tuple[str, int], ...],
    *,
    default: Optional[bool] = None,
) -> bool:
    raw_value = read_raw(config_data, path)
    if raw_value is None:
        if default is None:
            raise KeyError(path)
        else:
            return default

    if raw_value == "True":
        return True
    elif raw_value == "False":
        return False

    raise AssertionError(
        f"Unexpected value '{raw_value}' for expected boolean at path {path}"
    )


def read_str(
    config_data: Dict[Tuple[Tuple[str, int], ...], Any],
    path: Tuple[Tuple[str, int], ...],
    *,
    default: Optional[str] = None,
) -> str:
    # N.B.: The string localization data stores the English string in a comment section.
    #       Do not use the regular read_raw() function, since that will strip the comment!
    raw_value = config_data.get(path, default)
    if raw_value is None:
        if default is None:
            raise KeyError(path)
        else:
            return default

    if raw_value.startswith("#autoLOC"):
        match = localization_pattern.match(raw_value)
        if match is None:
            raise AssertionError(
                f"Found a localization-like string at path {path} that did not match "
                f"the expected localization pattern: {raw_value}"
            )
        else:
            return match.group("english").replace("\\n", "\n").strip()
    else:
        return raw_value
