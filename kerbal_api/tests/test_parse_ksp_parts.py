import os
import unittest

from ..cfg_parser.file_finder import get_cfg_files_recursively
from ..cfg_parser.parser import load_part_config_from_cfg_file
from ..utils import get_ksp_install_path


class KSPPartParsing(unittest.TestCase):
    def setUp(self) -> None:
        self.ksp_path = get_ksp_install_path()

    def test_ksp_base_game_parts_parse_without_errors(self) -> None:
        squad_dir_path = os.path.join(self.ksp_path, "GameData", "Squad", "Parts")

        files_processed = 0

        for file_path in get_cfg_files_recursively(squad_dir_path):
            files_processed += 1

            # This line is the code under test -- it is expected to not error.
            load_part_config_from_cfg_file(file_path)

        self.assertGreater(files_processed, 200)

    def test_ksp_expansion_parts_parse_without_errors(self) -> None:
        expansions_dir_path = os.path.join(
            self.ksp_path, "GameData", "SquadExpansion", "**", "Parts",
        )

        files_processed = 0

        for file_path in get_cfg_files_recursively(expansions_dir_path):
            files_processed += 1

            # This line is the code under test -- it is expected to not error.
            load_part_config_from_cfg_file(file_path)

        self.assertGreater(files_processed, 100)
