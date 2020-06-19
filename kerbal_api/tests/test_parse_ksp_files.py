from itertools import chain
import os
from typing import List
import unittest

from ..cfg_parser.file_finder import get_cfg_files_recursively
from ..cfg_parser.parser import parse_cfg_file
from ..querying.tokens import make_part_token
from ..utils import get_ksp_install_path


class KSPParsing(unittest.TestCase):
    def setUp(self) -> None:
        self.ksp_path = get_ksp_install_path()

        self.squad_dir_path = os.path.join(self.ksp_path, "GameData", "Squad")
        self.expansions_dir_path = os.path.join(self.ksp_path, "GameData", "SquadExpansion")

        self.squad_parts_dir_path = os.path.join(self.squad_dir_path, "Parts")
        self.expansions_parts_dir_path = os.path.join(self.expansions_dir_path, "**", "Parts")

    def test_ksp_base_game_files_parse_without_errors(self) -> None:
        files_processed = 0

        for file_path in get_cfg_files_recursively(self.squad_dir_path):
            files_processed += 1

            # This line is the code under test -- it is expected to not error.
            parse_cfg_file(file_path)

        self.assertGreater(files_processed, 450)

    def test_ksp_expansion_files_parse_without_errors(self) -> None:
        files_processed = 0

        for file_path in get_cfg_files_recursively(self.expansions_dir_path):
            files_processed += 1

            # This line is the code under test -- it is expected to not error.
            parse_cfg_file(file_path)

        self.assertGreater(files_processed, 200)

    def test_few_cfg_files_in_parts_dirs_that_are_semantically_confusing(self) -> None:
        # The game has a much broader definition of "part" than we'd like to use. For us,
        # a part means a thing we can use in the VAB/SPH and attach to our creations.
        # However, in the game, Kerbals on EVA are parts, and so are flags. We ignore these,
        # but here we make sure there aren't too many of them -- or we might be hiding bugs.
        non_part_files: List[str] = []

        all_stock_cfg_files = chain(
            get_cfg_files_recursively(self.squad_parts_dir_path),
            get_cfg_files_recursively(self.expansions_parts_dir_path),
        )
        for file_path in all_stock_cfg_files:
            part_config = parse_cfg_file(file_path)
            if part_config is None:
                non_part_files.append(file_path)
            else:
                part_token = make_part_token(file_path, part_config)
                if part_token is None:
                    non_part_files.append(file_path)

        self.assertLess(
            len(non_part_files),
            25,
            msg=f"Expected a small-ish list of files (<25), but got {non_part_files}",
        )
