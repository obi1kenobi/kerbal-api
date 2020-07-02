from typing import Any, ClassVar, Dict, List
from unittest import TestCase

import pytest

from ..querying import KerbalDataAdapter, execute_query, get_default_adapter


def ensure_query_produces_expected_output(
    test_case: "TestInterpreter",
    query: str,
    args: Dict[str, Any],
    expected_results: List[Dict[str, Any]],
) -> None:
    # The interpreter's output isn't ordered in any particular way, so this helper function
    # implements order-agnostic output comparisons.
    #
    # TODO: when @fold is implemented and tested, make sure we account for differences in
    #       result ordering within the @fold-ed outputs as well.

    actual_results = list(execute_query(test_case.adapter, query, args))

    test_case.assertCountEqual(expected_results, actual_results)


class TestInterpreter(TestCase):
    adapter: ClassVar[KerbalDataAdapter]

    @classmethod
    def setUpClass(cls) -> None:
        cls.adapter = get_default_adapter()

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
                "part_name": "A potato like comet",
                "internal_name": "PotatoComet",
                "dry_mass": 150.0,
            },
            {
                "part_name": "Kerbodyne S4-512 Fuel Tank",
                "internal_name": "Size4_Tank_04",
                "dry_mass": 32.0,
            },
        ]

        ensure_query_produces_expected_output(self, query, args, expected_results)

    def test_potato_parts_can_be_looked_up(self) -> None:
        query = """
        {
            Part {
                name @output(out_name: "part_name")
                internal_name @filter(op_name: "has_substring", value: ["$internal_name_substr"])
                              @output(out_name: "internal_name")
                dry_mass @output(out_name: "dry_mass")
            }
        }
        """
        args: Dict[str, Any] = {
            "internal_name_substr": "Potato",
        }

        expected_results = [
            {"part_name": "A potato like rock", "internal_name": "PotatoRoid", "dry_mass": 150.0,},
            {
                "part_name": "A potato like comet",
                "internal_name": "PotatoComet",
                "dry_mass": 150.0,
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

    def test_parts_costly_to_develop(self) -> None:
        query = """
        {
            Part {
                development_cost @filter(op_name: ">=", value: ["$min_development_cost"])
                                 @output(out_name: "development_cost")
                cost @output(out_name: "part_cost")
                name @output(out_name: "part_name")
            }
        }
        """

        args: Dict[str, Any] = {"min_development_cost": 200_000}

        expected_results = [
            {
                "development_cost": 204800,
                "part_cost": 51200,
                "part_name": "Kerbodyne S4-512 Fuel Tank",
            }
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
        expected_results: List[Dict[str, Any]] = [
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
                dry_mass @output(out_name: "dry_mass")

                out_Part_HasDefaultResource {
                    amount @output(out_name: "amount")
                    max_amount @output(out_name: "max_amount")

                    out_ContainedResource_Resource {
                        name @output(out_name: "resource_name")
                        density @output(out_name: "resource_density")
                    }
                }
            }
        }
        """
        args: Dict[str, Any] = {"internal_name": "Size2LFB"}

        expected_results = [
            {
                "part_name": 'LFB KR-1x2 "Twin-Boar" Liquid Fuel Engine',
                "dry_mass": 10.5,
                "resource_name": "Liquid Fuel",
                "amount": 2880.0,
                "max_amount": 2880.0,
                "resource_density": 0.005,
            },
            {
                "part_name": 'LFB KR-1x2 "Twin-Boar" Liquid Fuel Engine',
                "dry_mass": 10.5,
                "resource_name": "Oxidizer",
                "amount": 3520.0,
                "max_amount": 3520.0,
                "resource_density": 0.005,
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
                specific_volume @output(out_name: "specific_volume")
            }
        }
        """
        args: Dict[str, Any] = {"internal_name": "LiquidFuel"}

        expected_results = [
            {
                "resource_name": "Liquid Fuel",
                "density": 0.005,
                "specific_heat": 2010.0,
                "specific_volume": 5.0,
            },
        ]

        ensure_query_produces_expected_output(self, query, args, expected_results)

    def test_tech_tree_mandatory_prerequisites(self) -> None:
        query = """
        {
            Technology {
                name @filter(op_name: "=", value: ["$tech_name"]) @output(out_name: "tech_name")
                description @output(out_name: "tech_description")
                science_cost @output(out_name: "tech_cost")

                out_Technology_MandatoryPrerequisite {
                    name @output(out_name: "mandatory_prerequisite")
                    description @output(out_name: "prereq_description")
                    science_cost @output(out_name: "prereq_cost")
                }
            }
        }
        """
        args: Dict[str, Any] = {"tech_name": "Heavy Landing"}

        expected_results = [
            {
                "tech_name": "Heavy Landing",
                "tech_description": (
                    "A good landing is one where you walk away from it. "
                    "A great landing is one where you get to use the aircraft again."
                ),
                "tech_cost": 300.0,
                "mandatory_prerequisite": "Advanced Landing",
                "prereq_description": (
                    "Further advances in landing devices, allowing for more controlled descents "
                    "and a much higher number of parts still attached to the ship after touchdown."
                ),
                "prereq_cost": 160.0,
            },
        ]

        ensure_query_produces_expected_output(self, query, args, expected_results)

    def test_tech_tree_singular_any_of_prereqs_converted_to_mandatory_prerequisites(self) -> None:
        # This test ensures we correct a particular kind of data error in the game files,
        # where a tech is listed as having "any of" prerequisites, but only a single prerequisite
        # is listed. Since there is no choice to be made, we convert this to a mandatory prereq.
        query = """
        {
            Technology {
                name @filter(op_name: "=", value: ["$tech_name"]) @output(out_name: "tech_name")
                description @output(out_name: "tech_description")
                science_cost @output(out_name: "tech_cost")

                out_Technology_MandatoryPrerequisite {
                    name @output(out_name: "mandatory_prerequisite")
                    description @output(out_name: "prereq_description")
                    science_cost @output(out_name: "prereq_cost")
                }
            }
        }
        """
        args: Dict[str, Any] = {"tech_name": "Aviation"}

        expected_results = [
            {
                "tech_name": "Aviation",
                "tech_description": (
                    "The art and science of keeping heavier-than-air objects aloft "
                    "for extended periods of time."
                ),
                "tech_cost": 45.0,
                "mandatory_prerequisite": "Stability",
                "prereq_description": (
                    "Reaching for the stars starts with keeping our spacecraft "
                    "pointed generally in the right direction."
                ),
                "prereq_cost": 18.0,
            },
        ]

        ensure_query_produces_expected_output(self, query, args, expected_results)

    def test_tech_tree_any_of_prerequisites(self) -> None:
        query = """
        {
            Technology {
                name @filter(op_name: "=", value: ["$tech_name"]) @output(out_name: "tech_name")
                description @output(out_name: "tech_description")
                science_cost @output(out_name: "tech_cost")

                out_Technology_AnyOfPrerequisite {
                    name @output(out_name: "optional_prerequisite")
                    description @output(out_name: "prereq_description")
                    science_cost @output(out_name: "prereq_cost")
                }
            }
        }
        """
        args: Dict[str, Any] = {"tech_name": "Landing"}

        expected_results = [
            {
                "tech_name": "Landing",
                "tech_description": "Our Engineers are nothing if not optimistic.",
                "tech_cost": 90.0,
                "optional_prerequisite": "Flight Control",
                "prereq_description": (
                    "Tumbling out of control may be fun, but our engineers insist "
                    "there's more to rocket science than that."
                ),
                "prereq_cost": 45.0,
            },
            {
                "tech_name": "Landing",
                "tech_description": "Our Engineers are nothing if not optimistic.",
                "tech_cost": 90.0,
                "optional_prerequisite": "Aviation",
                "prereq_description": (
                    "The art and science of keeping heavier-than-air objects aloft "
                    "for extended periods of time."
                ),
                "prereq_cost": 45.0,
            },
        ]

        ensure_query_produces_expected_output(self, query, args, expected_results)

    def test_tech_tree_longest_mandatory_prereqs_chain(self) -> None:
        # Here's a chain of 9 technologies with all-mandatory prerequisites. These techs have to
        # be researched in the specified order, with no room to maneuver around them.
        # It is the longest such chain in the game!
        query = """
        {
            Technology {
                name @output(out_name: "tech_name")
                science_cost @output(out_name: "tech_cost")

                out_Technology_MandatoryPrerequisite {
                    name @output(out_name: "prereq_1_name")
                    science_cost @output(out_name: "prereq_1_cost")

                    out_Technology_MandatoryPrerequisite {
                        name @output(out_name: "prereq_2_name")
                        science_cost @output(out_name: "prereq_2_cost")

                        out_Technology_MandatoryPrerequisite {
                            name @output(out_name: "prereq_3_name")
                            science_cost @output(out_name: "prereq_3_cost")

                            out_Technology_MandatoryPrerequisite {
                                name @output(out_name: "prereq_4_name")
                                science_cost @output(out_name: "prereq_4_cost")

                                out_Technology_MandatoryPrerequisite {
                                    name @output(out_name: "prereq_5_name")
                                    science_cost @output(out_name: "prereq_5_cost")

                                    out_Technology_MandatoryPrerequisite {
                                        name @output(out_name: "prereq_6_name")
                                        science_cost @output(out_name: "prereq_6_cost")

                                        out_Technology_MandatoryPrerequisite {
                                            name @output(out_name: "prereq_7_name")
                                            science_cost @output(out_name: "prereq_7_cost")

                                            out_Technology_MandatoryPrerequisite {
                                                name @output(out_name: "prereq_8_name")
                                                science_cost @output(out_name: "prereq_8_cost")
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        args: Dict[str, Any] = {}

        expected_results = [
            {
                "tech_name": "Experimental Electrics",
                "tech_cost": 1000.0,
                "prereq_1_name": "Specialized Electrics",
                "prereq_1_cost": 550.0,
                "prereq_2_name": "High-Power Electrics",
                "prereq_2_cost": 300.0,
                "prereq_3_name": "Advanced Electrics",
                "prereq_3_cost": 160.0,
                "prereq_4_name": "Electrics",
                "prereq_4_cost": 90.0,
                "prereq_5_name": "Basic Science",
                "prereq_5_cost": 45.0,
                "prereq_6_name": "Survivability",
                "prereq_6_cost": 15.0,
                "prereq_7_name": "Engineering 101",
                "prereq_7_cost": 5.0,
                "prereq_8_name": "Start",
                "prereq_8_cost": 0.0,
            }
        ]

        ensure_query_produces_expected_output(self, query, args, expected_results)

    def test_tech_tree_longest_one_of_prereqs_chain(self) -> None:
        # Here's a chain of 7 technologies, all of which have "choose any" prerequisites.
        # For each of these techs except the start of the chain ("prereq_6"), the player
        # has a choice in how to unlock it based on which of the prerequisites they choose
        # to fulfill. They are the longest such chains in the game!
        query = """
        {
            Technology {
                name @output(out_name: "tech_name")
                science_cost @output(out_name: "tech_cost")

                out_Technology_AnyOfPrerequisite {
                    name @output(out_name: "prereq_1_name")
                    science_cost @output(out_name: "prereq_1_cost")

                    out_Technology_AnyOfPrerequisite {
                        name @output(out_name: "prereq_2_name")
                        science_cost @output(out_name: "prereq_2_cost")

                        out_Technology_AnyOfPrerequisite {
                            name @output(out_name: "prereq_3_name")
                            science_cost @output(out_name: "prereq_3_cost")

                            out_Technology_AnyOfPrerequisite {
                                name @output(out_name: "prereq_4_name")
                                science_cost @output(out_name: "prereq_4_cost")

                                out_Technology_AnyOfPrerequisite {
                                    name @output(out_name: "prereq_5_name")
                                    science_cost @output(out_name: "prereq_5_cost")

                                    out_Technology_AnyOfPrerequisite {
                                        name @output(out_name: "prereq_6_name")
                                        science_cost @output(out_name: "prereq_6_cost")
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        args: Dict[str, Any] = {}

        expected_results = [
            {
                "tech_name": "Very Heavy Rocketry",
                "tech_cost": 550.0,
                "prereq_1_name": "Large Volume Containment",
                "prereq_1_cost": 300.0,
                "prereq_2_name": "Adv. Fuel Systems",
                "prereq_2_cost": 160.0,
                "prereq_3_name": "Fuel Systems",
                "prereq_3_cost": 90.0,
                "prereq_4_name": "General Construction",
                "prereq_4_cost": 45.0,
                "prereq_5_name": "Stability",
                "prereq_5_cost": 18.0,
                "prereq_6_name": "Engineering 101",
                "prereq_6_cost": 5.0,
            },
            {
                "tech_name": "Very Heavy Rocketry",
                "tech_cost": 550.0,
                "prereq_1_name": "Large Volume Containment",
                "prereq_1_cost": 300.0,
                "prereq_2_name": "Adv. Fuel Systems",
                "prereq_2_cost": 160.0,
                "prereq_3_name": "Fuel Systems",
                "prereq_3_cost": 90.0,
                "prereq_4_name": "General Construction",
                "prereq_4_cost": 45.0,
                "prereq_5_name": "Stability",
                "prereq_5_cost": 18.0,
                "prereq_6_name": "Basic Rocketry",
                "prereq_6_cost": 5.0,
            },
        ]

        ensure_query_produces_expected_output(self, query, args, expected_results)

    def test_part_required_technology(self) -> None:
        query = """
        {
            Part {
                internal_name @filter(op_name: "=", value: ["$internal_name"])
                name @output(out_name: "part_name")

                out_Part_RequiredTechnology {
                    name @output(out_name: "requires_tech")
                    science_cost @output(out_name: "tech_cost")
                }
            }
        }
        """
        args: Dict[str, Any] = {"internal_name": "Size2LFB"}

        expected_results = [
            {
                "part_name": 'LFB KR-1x2 "Twin-Boar" Liquid Fuel Engine',
                "requires_tech": "Heavier Rocketry",
                "tech_cost": 160.0,
            },
        ]

        ensure_query_produces_expected_output(self, query, args, expected_results)

    def test_part_transmitter_module_basic_stats_loading(self) -> None:
        query = """
        {
            Part {
                internal_name @filter(op_name: "=", value: ["$internal_name"])

                out_Part_DataTransmitter {
                    power @output(out_name: "power")
                    packet_size @output(out_name: "packet_size")
                    packet_cost @output(out_name: "packet_cost")
                    packet_interval @output(out_name: "packet_interval")

                    transmission_speed @output(out_name: "transmission_speed")
                    electricity_per_mit @output(out_name: "electricity_per_mit")
                    electricity_per_second @output(out_name: "electricity_per_second")
                }
            }
        }
        """
        args: Dict[str, Any] = {"internal_name": "mk1pod"}

        expected_results = [
            {
                "power": 5000.0,
                "packet_size": 2.0,
                "packet_cost": 12.0,
                "packet_interval": 1.0,
                "transmission_speed": 2.0,
                "electricity_per_mit": 6.0,
                "electricity_per_second": 12.0,
            },
        ]

        ensure_query_produces_expected_output(self, query, args, expected_results)

    def test_part_transmitter_module_coercion_to_internal_transmitter_result_unchanged(
        self,
    ) -> None:
        query = """
        {
            Part {
                internal_name @filter(op_name: "=", value: ["$internal_name"])

                out_Part_DataTransmitter {
                    ... on InternalTransmitterModule {
                        power @output(out_name: "power")
                        packet_size @output(out_name: "packet_size")
                        packet_cost @output(out_name: "packet_cost")
                        packet_interval @output(out_name: "packet_interval")

                        transmission_speed @output(out_name: "transmission_speed")
                        electricity_per_mit @output(out_name: "electricity_per_mit")
                        electricity_per_second @output(out_name: "electricity_per_second")
                    }
                }
            }
        }
        """
        args: Dict[str, Any] = {"internal_name": "mk1pod"}

        expected_results = [
            {
                "power": 5000.0,
                "packet_size": 2.0,
                "packet_cost": 12.0,
                "packet_interval": 1.0,
                "transmission_speed": 2.0,
                "electricity_per_mit": 6.0,
                "electricity_per_second": 12.0,
            },
        ]

        ensure_query_produces_expected_output(self, query, args, expected_results)

    def test_part_transmitter_module_coercion_to_antenna_transmitter_no_results(self,) -> None:
        query = """
        {
            Part {
                internal_name @filter(op_name: "=", value: ["$internal_name"])

                out_Part_DataTransmitter {
                    ... on AntennaModule {
                        power @output(out_name: "power")
                        packet_size @output(out_name: "packet_size")
                        packet_cost @output(out_name: "packet_cost")
                        packet_interval @output(out_name: "packet_interval")

                        transmission_speed @output(out_name: "transmission_speed")
                        electricity_per_mit @output(out_name: "electricity_per_mit")
                        electricity_per_second @output(out_name: "electricity_per_second")
                    }
                }
            }
        }
        """
        args: Dict[str, Any] = {"internal_name": "mk1pod"}

        expected_results: List[Dict[str, Any]] = []

        ensure_query_produces_expected_output(self, query, args, expected_results)

    def test_part_transmitter_module_communotron_data(self) -> None:
        query = """
        {
            Part {
                name @filter(op_name: "has_substring", value: ["$name_substr"])
                     @output(out_name: "part_name")

                out_Part_DataTransmitter {
                    power @output(out_name: "power")
                    packet_size @output(out_name: "packet_size")
                    packet_cost @output(out_name: "packet_cost")
                    packet_interval @output(out_name: "packet_interval")
                }
            }
        }
        """
        args: Dict[str, Any] = {"name_substr": "Communotron"}

        expected_results: List[Dict[str, Any]] = [
            {
                "part_name": "Communotron HG-55",
                "power": 15000000000.0,
                "packet_size": 3.0,
                "packet_cost": 20.0,
                "packet_interval": 0.15,
            },
            {
                "part_name": "Communotron 88-88",
                "power": 100000000000.0,
                "packet_size": 2.0,
                "packet_cost": 20.0,
                "packet_interval": 0.1,
            },
            {
                "part_name": "Communotron DTS-M1",
                "power": 2000000000.0,
                "packet_size": 2.0,
                "packet_cost": 12.0,
                "packet_interval": 0.35,
            },
            {
                "part_name": "Communotron 16",
                "power": 500000.0,
                "packet_size": 2.0,
                "packet_cost": 12.0,
                "packet_interval": 0.6,
            },
            {
                "part_name": "Communotron 16-S",
                "power": 500000.0,
                "packet_size": 2.0,
                "packet_cost": 12.0,
                "packet_interval": 0.6,
            },
        ]

        ensure_query_produces_expected_output(self, query, args, expected_results)

    def test_part_transmitter_module_communotron_internal_transmitter_coercion_has_no_results(
        self,
    ) -> None:
        query = """
        {
            Part {
                name @filter(op_name: "has_substring", value: ["$name_substr"])
                     @output(out_name: "part_name")

                out_Part_DataTransmitter {
                    ... on InternalTransmitterModule {
                        power @output(out_name: "power")
                        packet_size @output(out_name: "packet_size")
                        packet_cost @output(out_name: "packet_cost")
                        packet_interval @output(out_name: "packet_interval")
                    }
                }
            }
        }
        """
        args: Dict[str, Any] = {"name_substr": "Communotron"}

        expected_results: List[Dict[str, Any]] = []

        ensure_query_produces_expected_output(self, query, args, expected_results)

    def test_part_transmitter_module_communotron_coercion_does_not_change_results(self) -> None:
        query = """
        {
            Part {
                name @filter(op_name: "has_substring", value: ["$name_substr"])
                     @output(out_name: "part_name")

                out_Part_DataTransmitter {
                    ... on AntennaModule {
                        power @output(out_name: "power")
                        packet_size @output(out_name: "packet_size")
                        packet_cost @output(out_name: "packet_cost")
                        packet_interval @output(out_name: "packet_interval")
                    }
                }
            }
        }
        """
        args: Dict[str, Any] = {"name_substr": "Communotron"}

        expected_results: List[Dict[str, Any]] = [
            {
                "part_name": "Communotron HG-55",
                "power": 15000000000.0,
                "packet_size": 3.0,
                "packet_cost": 20.0,
                "packet_interval": 0.15,
            },
            {
                "part_name": "Communotron 88-88",
                "power": 100000000000.0,
                "packet_size": 2.0,
                "packet_cost": 20.0,
                "packet_interval": 0.1,
            },
            {
                "part_name": "Communotron DTS-M1",
                "power": 2000000000.0,
                "packet_size": 2.0,
                "packet_cost": 12.0,
                "packet_interval": 0.35,
            },
            {
                "part_name": "Communotron 16",
                "power": 500000.0,
                "packet_size": 2.0,
                "packet_cost": 12.0,
                "packet_interval": 0.6,
            },
            {
                "part_name": "Communotron 16-S",
                "power": 500000.0,
                "packet_size": 2.0,
                "packet_cost": 12.0,
                "packet_interval": 0.6,
            },
        ]

        ensure_query_produces_expected_output(self, query, args, expected_results)

    def test_unresearchable_part_has_no_required_technology(self,) -> None:
        query = """
        {
            Part {
                internal_name @filter(op_name: "=", value: ["$name"])
                name @output(out_name: "part_name")

                out_Part_RequiredTechnology @optional {
                    name @output(out_name: "tech_required")
                }
            }
        }
        """
        args: Dict[str, Any] = {"name": "PotatoRoid"}

        expected_results: List[Dict[str, Any]] = [
            {"part_name": "A potato like rock", "tech_required": None,}
        ]

        ensure_query_produces_expected_output(self, query, args, expected_results)

    @pytest.mark.xfail(reason="Bug in the underlying GraphQL compiler interpreter prototype.")
    def test_mandatory_traversal_after_optional_traversal(self,) -> None:
        query = """
        {
            Part {
                internal_name @filter(op_name: "=", value: ["$name"])
                name @output(out_name: "part_name")

                out_Part_HasDefaultResource @optional {
                    out_ContainedResource_Resource {
                        name @output(out_name: "contained_resource")
                    }
                }
            }
        }
        """
        args: Dict[str, Any] = {"name": "PotatoRoid"}

        expected_results: List[Dict[str, Any]] = [
            {"part_name": "A potato like rock", "contained_resource": None,}
        ]

        ensure_query_produces_expected_output(self, query, args, expected_results)

    def test_fetch_every_edge_for_all_parts_does_not_error(self) -> None:
        query = """
        {
            Part {
                name @output(out_name: "part_name")

                out_Part_DataTransmitter @optional {
                    power @output(out_name: "transmitter_power")
                }
                out_Part_EngineModule @optional {
                    max_thrust @output(out_name: "engine_max_thrust")
                }
                out_Part_HasDefaultResource @optional {
                    out_ContainedResource_Resource {
                        name @output(out_name: "contained_resource")
                    }
                }
                out_Part_RequiredTechnology @optional {
                    name @output(out_name: "required_tech")
                }
            }
        }
        """
        args: Dict[str, Any] = {}

        # We are testing to make sure that looking up all of the above info does not produce
        # any errors, especially with regard to edge cases about special-cased parts like
        # the potato-asteroid, which is unresearchable and cannot be added to craft in the VAB/SPH.
        #
        # execute_query() returns a generator and lazily computes results. We have to drain the
        # generator to complete the execution, even though we don't care about the results.
        for _ in execute_query(self.adapter, query, args):
            pass
