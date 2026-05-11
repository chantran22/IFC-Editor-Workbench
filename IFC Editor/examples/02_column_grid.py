"""
Example 02 - Column Grid
=========================
3x4 grid of circular RC columns, 400mm dia x 4m high.
Press F5 to run.
"""

import numpy as np
import ifcopenshell.api.unit
import ifcopenshell.api.context
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.api.aggregate
import ifcopenshell.api.geometry
import ifcopenshell.api.material

# --- Project FIRST ---
project  = ifcopenshell.api.root.create_entity(model, ifc_class="IfcProject", name="Column Grid")
ifcopenshell.api.unit.assign_unit(model, length={"is_metric": True, "raw": "METRES"})

ctx  = ifcopenshell.api.context.add_context(model, context_type="Model")
body = ifcopenshell.api.context.add_context(model,
    context_type="Model", context_identifier="Body",
    target_view="MODEL_VIEW", parent=ctx)

site     = ifcopenshell.api.root.create_entity(model, ifc_class="IfcSite",           name="Site")
building = ifcopenshell.api.root.create_entity(model, ifc_class="IfcBuilding",       name="Structure")
storey   = ifcopenshell.api.root.create_entity(model, ifc_class="IfcBuildingStorey", name="L1")
for p, c in [(project,site),(site,building),(building,storey)]:
    ifcopenshell.api.aggregate.assign_object(model, relating_object=p, products=[c])

mat = ifcopenshell.api.material.add_material(model, name="RC C35/45", category="concrete")

# --- Grid parameters ---
ROWS=3; COLS=4; SPACING_X=6.0; SPACING_Y=7.0; RADIUS=0.2; HEIGHT=4.0

z_dir = model.create_entity("IfcDirection", DirectionRatios=(float(0.0), float(0.0), float(1.0)))

for row in range(ROWS):
    for col in range(COLS):
        x = col * SPACING_X
        y = row * SPACING_Y

        ax2_2d  = model.create_entity("IfcAxis2Placement2D",
                      Location=model.create_entity("IfcCartesianPoint", Coordinates=(float(0.0), float(0.0))))
        profile = model.create_entity("IfcCircleProfileDef",
                      ProfileType="AREA", Radius=RADIUS, Position=ax2_2d)
        origin  = model.create_entity("IfcCartesianPoint", Coordinates=(float(x), float(y), float(0.0)))
        axis3   = model.create_entity("IfcAxis2Placement3D", Location=origin, Axis=z_dir)
        extr    = model.create_entity("IfcExtrudedAreaSolid",
                      SweptArea=profile, Position=axis3,
                      ExtrudedDirection=z_dir, Depth=HEIGHT)
        rep     = model.create_entity("IfcShapeRepresentation",
                      ContextOfItems=body,
                      RepresentationIdentifier="Body",
                      RepresentationType="SweptSolid",
                      Items=[extr])
        shape   = model.create_entity("IfcProductDefinitionShape", Representations=[rep])

        tag    = f"COL-R{row+1:02d}-C{col+1:02d}"
        column = ifcopenshell.api.root.create_entity(model, ifc_class="IfcColumn", name=tag)
        column.Representation = shape
        ifcopenshell.api.spatial.assign_container(model, relating_structure=storey, products=[column])
        ifcopenshell.api.geometry.edit_object_placement(model, product=column, matrix=np.eye(4))
        ifcopenshell.api.material.assign_material(model, products=[column], material=mat)

print(f"Created {ROWS*COLS} columns  ({ROWS}x{COLS})  spacing {SPACING_X}x{SPACING_Y}m")
