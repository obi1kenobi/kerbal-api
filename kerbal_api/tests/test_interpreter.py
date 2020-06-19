from typing import Any, Dict, List
from unittest import TestCase

from ..querying import execute_query, get_default_adapter


def ensure_query_produces_expected_output(
    test_case: TestCase, query: str, args: Dict[str, Any], expected_results: List[Dict[str, Any]],
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
    def setUp(self) -> None:
        self.maxDiff = None

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
            {"part_name": "A potato like rock", "internal_name": "PotatoRoid", "dry_mass": 150.0,},
            {
                "part_name": "Kerbodyne S4-512 Fuel Tank",
                "internal_name": "Size4_Tank_04",
                "dry_mass": 32.0,
            },
        ]

        ensure_query_produces_expected_output(self, query, args, expected_results)

    def test_part_lookup_by_name_substring(self) -> None:
        query = """
        {
            Part {
                name @filter(op_name: "has_substring", value: ["$name_substr"])
                     @output(out_name: "part_name")
                internal_name @output(out_name: "internal_name")
                dry_mass @output(out_name: "dry_mass")
                max_temp_tolerance @output(out_name: "temp_tolerance")
                crash_tolerance @output(out_name: "crash_tolerance")
            }
        }
        """
        args: Dict[str, Any] = {"name_substr": "Landing Strut"}

        expected_results = [
            {
                "part_name": "LT-1 Landing Struts",
                "internal_name": "landingLeg1",
                "dry_mass": 0.05,
                "temp_tolerance": 2000.0,
                "crash_tolerance": 12.0,
            },
            {
                "part_name": "LT-2 Landing Strut",
                "internal_name": "landingLeg1-2",
                "dry_mass": 0.1,
                "temp_tolerance": 2000.0,
                "crash_tolerance": 12.0,
            },
            {
                "part_name": "LT-05 Micro Landing Strut",
                "internal_name": "miniLandingLeg",
                "dry_mass": 0.015,
                "temp_tolerance": 1200.0,
                "crash_tolerance": 10.0,
            },
        ]

        ensure_query_produces_expected_output(self, query, args, expected_results)

    def test_engine_part_edge_traversal(self) -> None:
        query = """
        {
            Part {
                internal_name @filter(op_name: "=", value: ["$internal_name"])
                cost @output(out_name: "part_cost")
                dry_mass @output(out_name: "part_dry_mass")

                out_Part_EngineModule {
                    min_thrust @output(out_name: "min_thrust")
                    max_thrust @output(out_name: "max_thrust")
                    throttleable @output(out_name: "throttleable")
                    isp_vacuum @output(out_name: "isp_vacuum")
                    isp_at_1atm @output(out_name: "isp_at_1atm")
                }
            }
        }
        """
        args: Dict[str, Any] = {"internal_name": "RAPIER"}

        # The RAPIER engine has two engine modes, and therefore two engine modules.
        expected_results = [
            {
                "part_cost": 6000,
                "part_dry_mass": 2.0,
                "min_thrust": 0.0,
                "max_thrust": 105.0,
                "throttleable": True,
                "isp_vacuum": 3200.0,
                "isp_at_1atm": None,
            },
            {
                "part_cost": 6000,
                "part_dry_mass": 2.0,
                "min_thrust": 0.0,
                "max_thrust": 180.0,
                "throttleable": True,
                "isp_vacuum": 305.0,
                "isp_at_1atm": 275.0,
            },
        ]

        ensure_query_produces_expected_output(self, query, args, expected_results)

    def test_contained_resource_traversal(self) -> None:
        query = """
        {
            Part {
                internal_name @filter(op_name: "=", value: ["$internal_name"])
                name @output(out_name: "part_name")

                out_Part_HasDefaultResource {
                    resource_internal_name @output(out_name: "resource_name")
                    amount @output(out_name: "amount")
                    max_amount @output(out_name: "max_amount")
                }
            }
        }
        """
        args: Dict[str, Any] = {"internal_name": "Size2LFB"}

        expected_results = [
            {
                "part_name": 'LFB KR-1x2 "Twin-Boar" Liquid Fuel Engine',
                "resource_name": "LiquidFuel",
                "amount": 2880.0,
                "max_amount": 2880.0,
            },
            {
                "part_name": 'LFB KR-1x2 "Twin-Boar" Liquid Fuel Engine',
                "resource_name": "Oxidizer",
                "amount": 3520.0,
                "max_amount": 3520.0,
            },
        ]

        ensure_query_produces_expected_output(self, query, args, expected_results)

    def test_resource_info(self) -> None:
        query = """
        {
            Resource {
                internal_name @filter(op_name: "=", value: ["$internal_name"])
                name @output(out_name: "resource_name")
                density @output(out_name: "density")
                specific_heat @output(out_name: "specific_heat")
                volume @output(out_name: "volume")
            }
        }
        """
        args: Dict[str, Any] = {"internal_name": "LiquidFuel"}

        expected_results = [
            {
                "resource_name": "Liquid Fuel",
                "density": 0.005,
                "specific_heat": 2010.0,
                "volume": 8,
            },
        ]
