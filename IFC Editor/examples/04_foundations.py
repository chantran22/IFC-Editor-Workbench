"""
Example 04 - Foundation Grid
==============================
Pad footings + columns on a 3x4 grid. No mathutils needed.
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

# --- Setup ---
project  = ifcopenshell.api.root.create_entity(model, ifc_class="IfcProject", name="Foundation Demo")
ifcopenshell.api.unit.assign_unit(model, length={"is_metric": True, "raw": "METRES"})

ctx  = ifcopenshell.api.context.add_context(model, context_type="Model")
body = ifcopenshell.api.context.add_context(model,
    context_type="Model", context_identifier="Body",
    target_view="MODEL_VIEW", parent=ctx)

site     = ifcopenshell.api.root.create_entity(model, ifc_class="IfcSite",           name="Site")
building = ifcopenshell.api.root.create_entity(model, ifc_class="IfcBuilding",       name="Building")
storey   = ifcopenshell.api.root.create_entity(model, ifc_class="IfcBuildingStorey", name="Foundation")

ifcopenshell.api.aggregate.assign_object(model, relating_object=project,  products=[site])
ifcopenshell.api.aggregate.assign_object(model, relating_object=site,      products=[building])
ifcopenshell.api.aggregate.assign_object(model, relating_object=building,  products=[storey])

mat_conc = ifcopenshell.api.material.add_material(model, name="Concrete C30", category="concrete")

# --- Grid parameters ---
ROWS      = 3
COLS      = 4
SPACING_X = 6.0
SPACING_Y = 7.0

# Footing
FTG_W = 1.5
FTG_L = 1.5
FTG_D = 0.6

# Column above footing
COL_R = 0.25
COL_H = 4.0

z_dir = model.create_entity("IfcDirection", DirectionRatios=(float(0.0), float(0.0), float(1.0)))
x_dir = model.create_entity("IfcDirection", DirectionRatios=(float(1.0), float(0.0), float(0.0)))

def make_rect_solid(xdim, ydim, depth, x, y, z):
    origin  = model.create_entity("IfcCartesianPoint", Coordinates=(float(x), float(y), float(z)))
    profile = model.create_entity("IfcRectangleProfileDef",
                  ProfileType="AREA", XDim=xdim, YDim=ydim)
    axis3   = model.create_entity("IfcAxis2Placement3D",
                  Location=origin, Axis=z_dir, RefDirection=x_dir)
    extr    = model.create_entity("IfcExtrudedAreaSolid",
                  SweptArea=profile, Position=axis3,
                  ExtrudedDirection=z_dir, Depth=depth)
    rep     = model.create_entity("IfcShapeRepresentation",
                  ContextOfItems=body,
                  RepresentationIdentifier="Body",
                  RepresentationType="SweptSolid",
                  Items=[extr])
    return model.create_entity("IfcProductDefinitionShape", Representations=[rep])

def make_circle_solid(radius, depth, x, y, z):
    ax2_2d  = model.create_entity("IfcAxis2Placement2D",
                  Location=model.create_entity("IfcCartesianPoint", Coordinates=(float(0.0), float(0.0))))
    profile = model.create_entity("IfcCircleProfileDef",
                  ProfileType="AREA", Radius=radius, Position=ax2_2d)
    origin  = model.create_entity("IfcCartesianPoint", Coordinates=(float(x), float(y), float(z)))
    axis3   = model.create_entity("IfcAxis2Placement3D", Location=origin, Axis=z_dir)
    extr    = model.create_entity("IfcExtrudedAreaSolid",
                  SweptArea=profile, Position=axis3,
                  ExtrudedDirection=z_dir, Depth=depth)
    rep     = model.create_entity("IfcShapeRepresentation",
                  ContextOfItems=body,
                  RepresentationIdentifier="Body",
                  RepresentationType="SweptSolid",
                  Items=[extr])
    return model.create_entity("IfcProductDefinitionShape", Representations=[rep])

for row in range(ROWS):
    for col in range(COLS):
        x = col * SPACING_X
        y = row * SPACING_Y

        # Pad footing (below ground)
        ftg = ifcopenshell.api.root.create_entity(model, ifc_class="IfcFooting",
                  name=f"FTG-R{row+1:02d}-C{col+1:02d}",
                  predefined_type="PAD_FOOTING")
        ftg.Representation = make_rect_solid(FTG_W, FTG_L, FTG_D, x, y, -FTG_D)
        ifcopenshell.api.spatial.assign_container(model, relating_structure=storey, products=[ftg])
        ifcopenshell.api.geometry.edit_object_placement(model, product=ftg, matrix=np.eye(4))
        ifcopenshell.api.material.assign_material(model, products=[ftg], material=mat_conc)

        # Column above footing
        col_obj = ifcopenshell.api.root.create_entity(model, ifc_class="IfcColumn",
                      name=f"COL-R{row+1:02d}-C{col+1:02d}")
        col_obj.Representation = make_circle_solid(COL_R, COL_H, x, y, 0.0)
        ifcopenshell.api.spatial.assign_container(model, relating_structure=storey, products=[col_obj])
        ifcopenshell.api.geometry.edit_object_placement(model, product=col_obj, matrix=np.eye(4))
        ifcopenshell.api.material.assign_material(model, products=[col_obj], material=mat_conc)

print(f"Created {ROWS*COLS} footings + {ROWS*COLS} columns")
