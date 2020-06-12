from typing import Any, Dict, Iterable, Tuple

from graphql_compiler.interpreter import DataContext, InterpreterAdapter
from graphql_compiler.interpreter.typedefs import EdgeInfo

from .data_manager import KerbalDataManager, get_engine_modules_for_part
from .tokens import KerbalToken


class KerbalDataAdapter(InterpreterAdapter[KerbalToken]):
    ksp_install_path: str
    data_manager: KerbalDataManager

    def __init__(self, ksp_install_path: str) -> None:
        self.ksp_install_path = ksp_install_path
        self.data_manager = KerbalDataManager.from_ksp_install_path(ksp_install_path)

    def get_tokens_of_type(self, type_name: str, **hints: Dict[str, Any]) -> Iterable[KerbalToken]:
        if type_name == "Part":
            return self.data_manager.parts
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
        edge_info: EdgeInfo,
        **hints: Dict[str, Any],
    ) -> Iterable[Tuple[DataContext[KerbalToken], Iterable[KerbalToken]]]:
        for data_context in data_contexts:
            token = data_context.current_token

            if token is None:
                yield (data_context, [])
                continue

            if (current_type_name, edge_info) == ("Part", ("out", "Part_EngineModule")):
                yield (data_context, get_engine_modules_for_part(self.data_manager, token))
            else:
                raise NotImplementedError()

    def can_coerce_to_type(
        self,
        data_contexts: Iterable[DataContext[KerbalToken]],
        current_type_name: str,
        coerce_to_type_name: str,
        **hints: Dict[str, Any],
    ) -> Iterable[Tuple[DataContext[KerbalToken], bool]]:
        raise NotImplementedError()
