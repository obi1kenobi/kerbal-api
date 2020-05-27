from typing import Any, Dict, Iterable, Tuple

from graphql_compiler.interpreter import InterpreterAdapter, DataContext, DataToken

from ..cfg_parser.file_finder import get_ksp_part_cfg_files
from .schema import KSP_SCHEMA
from .tokens import KerbalToken, make_part_token


class KerbalDataAdapter(InterpreterAdapter[KerbalToken]):
    ksp_install_path: str

    def __init__(self, ksp_install_path: str) -> None:
        self.ksp_install_path = ksp_install_path

    def get_tokens_of_type(
        self,
        type_name: str,
        **hints: Dict[str, Any],
    ) -> Iterable[KerbalToken]:
        if type_name == "Part":
            for cfg_file in get_ksp_part_cfg_files(self.ksp_install_path):
                part_token = make_part_token(cfg_file)
                if part_token is not None:
                    yield part_token
        else:
            raise NotImplementedError()

    def project_property(
        self,
        data_contexts: Iterable[DataContext[KerbalToken]],
        current_type_name: str,
        field_name: str,
        **hints: Dict[str, Any],
    ) -> Iterable[Tuple[DataContext[KerbalToken], Any]]:
        for data_context in data_contexts:
            token = data_context.current_token
            current_value = None
            if token is not None:
                current_value = token.content[field_name]

            yield (data_context, current_value)

    def project_neighbors(
        self,
        data_contexts: Iterable[DataContext[KerbalToken]],
        current_type_name: str,
        direction: str,
        edge_name: str,
        **hints: Dict[str, Any],
    ) -> Iterable[Tuple[DataContext[KerbalToken], Iterable[KerbalToken]]]:
        raise NotImplementedError()

    def can_coerce_to_type(
        self,
        data_contexts: Iterable[DataContext[KerbalToken]],
        current_type_name: str,
        coerce_to_type_name: str,
        **hints: Dict[str, Any],
    ) -> Iterable[Tuple[DataContext[KerbalToken], bool]]:
        raise NotImplementedError()
