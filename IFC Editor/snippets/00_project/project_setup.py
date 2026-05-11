"""
Project Setup — correct IFC spatial hierarchy.
IfcProject aggregates Site/Building — NOT assign_container.
assign_container is only for Building -> Storey -> Elements.
"""

import ifcopenshell.api.unit
import ifcopenshell.api.context
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.api.aggregate

# 1. Project FIRST
project  = ifcopenshell.api.root.create_entity(model, ifc_class="IfcProject",        name="My Project")

# 2. Units (needs IfcProject)
ifcopenshell.api.unit.assign_unit(model, length={"is_metric": True, "raw": "METRES"})

# 3. Geometry contexts
ctx  = ifcopenshell.api.context.add_context(model, context_type="Model")
body = ifcopenshell.api.context.add_context(model,
    context_type="Model", context_identifier="Body",
    target_view="MODEL_VIEW", parent=ctx)

# 4. Spatial hierarchy — use aggregate for project/site/building levels
site     = ifcopenshell.api.root.create_entity(model, ifc_class="IfcSite",           name="Site")
building = ifcopenshell.api.root.create_entity(model, ifc_class="IfcBuilding",       name="Building")
storey   = ifcopenshell.api.root.create_entity(model, ifc_class="IfcBuildingStorey", name="Level 1")

ifcopenshell.api.aggregate.assign_object(model, relating_object=project,  products=[site])
ifcopenshell.api.aggregate.assign_object(model, relating_object=site,      products=[building])
ifcopenshell.api.aggregate.assign_object(model, relating_object=building,  products=[storey])

# NOTE: assign_container is used ONLY for elements inside a storey, e.g.:
# ifcopenshell.api.spatial.assign_container(model, relating_structure=storey, products=[wall])
