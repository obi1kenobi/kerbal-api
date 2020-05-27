from typing import Any, Dict, List
from unittest import TestCase

from ..querying import execute_query, get_default_adapter


def ensure_query_produces_expected_output(
    test_case: TestCase,
    query: str,
    args: Dict[str, Any],
    expected_results: List[Dict[str, Any]],
) -> None:
    # The interpreter's output isn't ordered in any particular way, so this helper function
    # implements order-agnostic output comparisons.
    #
    # TODO: when @fold is implemented and tested, make sure we account for differences in
    #       result ordering within the @fold-ed outputs as well.
    adapter = get_default_adapter()

    actual_results = list(execute_query(adapter, query, args))

    test_case.assertCountEqual(expected_results, actual_results)


class TestInterpreter(TestCase):
    def test_high_weight_objects_are_retrieved_correctly(self) -> None:
        query = """
        {
            Part {
                name @output(out_name: "part_name")
                internal_name @output(out_name: "internal_name")
                dry_mass @filter(op_name: ">=", value: ["$min_mass"]) @output(out_name: "dry_mass")
            }
        }
        """
        args: Dict[str, Any] = {
            "min_mass": 20.0,
        }

        expected_results = [
            {
                "part_name": 'S2-33 "Clydesdale" Solid Fuel Booster',
                "internal_name": "Clydesdale",
                "dry_mass": 21.0,
            },
            {
                "part_name": "A potato like rock",
                "internal_name": "PotatoRoid",
                "dry_mass": 150.0,
            },
            {
                "part_name": "Kerbodyne S4-512 Fuel Tank",
                "internal_name": "Size4_Tank_04",
                "dry_mass": 32.0,
            },
        ]

        ensure_query_produces_expected_output(self, query, args, expected_results)
