from typing import Any, Dict, Iterable

from graphql_compiler.compiler.compiler_frontend import graphql_to_ir
from graphql_compiler.interpreter import interpret_ir

from ..utils import get_ksp_install_path
from .interpreter import KerbalDataAdapter
from .schema import KSP_SCHEMA


def get_default_adapter() -> KerbalDataAdapter:
    return KerbalDataAdapter(get_ksp_install_path())


def execute_query(
    adapter: KerbalDataAdapter, query: str, args: Dict[str, Any],
) -> Iterable[Dict[str, Any]]:
    ir_and_metadata = graphql_to_ir(KSP_SCHEMA, query)
    return interpret_ir(adapter, ir_and_metadata, args)
