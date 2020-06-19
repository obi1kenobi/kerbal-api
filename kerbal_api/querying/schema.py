from graphql import build_ast_schema, parse


# TODO: Grab these definitions directly from the GraphQL compiler package instead.
SCHEMA_BASE = """
schema {
    query: RootSchemaQuery
}

directive @filter(
    \"\"\"Name of the filter operation to perform.\"\"\"
    op_name: String!
    \"\"\"List of string operands for the operator.\"\"\"
    value: [String!]
) repeatable on FIELD | INLINE_FRAGMENT

directive @tag(
    \"\"\"Name to apply to the given property field.\"\"\"
    tag_name: String!
) on FIELD

directive @output(
    \"\"\"What to designate the output field generated from this property field.\"\"\"
    out_name: String!
) on FIELD

directive @output_source on FIELD

directive @optional on FIELD

directive @recurse(
    \"\"\"
    Recurse up to this many times on this edge. A depth of 1 produces the current
    vertex and its immediate neighbors along the given edge.
    \"\"\"
    depth: Int!
) on FIELD

directive @fold on FIELD

directive @macro_edge on FIELD_DEFINITION

directive @stitch(source_field: String!, sink_field: String!) on FIELD_DEFINITION
"""

KSP_SCHEMA_TEXT = (
    SCHEMA_BASE
    + """

type Part {
    cfg_file_path: String
    internal_name: String
    name: String
    manufacturer: String
    description: String
    cost: Int
    dry_mass: Float  # expressed in metric tons
    crash_tolerance: Float  # expressed in m/s
    max_temp_tolerance: Float  # expressed in Kelvin, part explodes if above this temp

    out_Part_EngineModule: [EngineModule]
    out_Part_HasDefaultResource: [ContainedResource]
    out_Part_RequiredTechnology: [Technology]
}

type EngineModule {
    min_thrust: Float
    max_thrust: Float
    throttleable: Boolean  # e.g., solid boosters cannot be throttled down
    isp_vacuum: Float
    isp_at_1atm: Float
}

type ContainedResource {
    amount: Float  # current amount
    max_amount: Float  # maximum possible amount

    out_ContainedResource_Resource: [Resource]
}

type Resource {
    cfg_file_path: String
    internal_name: String
    name: String
    density: Float  # measured in tons per unit of resource
    specific_heat: Float  # amount of thermal energy required to raise temperature by 1 degree
    unit_cost: Float  # cost per unit of resource
    specific_volume: Float  # volume per unit of resource
}

type Technology {
    cfg_file_path: String
    id: String
    name: String
    description: String
    science_cost: Float

    out_Technology_MandatoryPrerequisite: [Technology]  # to unlock this tech, unlock all of these
    out_Technology_AnyOfPrerequisite: [Technology]  # to unlock this tech, unlock any of these

    # TODO: add these "opposite direction" edges
    # in_Technology_MandatoryPrerequisite: [Technology]  # this tech is a prereq for the following
    # in_Technology_AnyOfPrerequisite: [Technology]  # this is an "any of" prereq for the following
}

type RootSchemaQuery {
    Part: [Part]
    Resource: [Resource]
    Technology: [Technology]
}
"""
)

KSP_SCHEMA = build_ast_schema(parse(KSP_SCHEMA_TEXT))
