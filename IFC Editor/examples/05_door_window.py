"""
Example 05 - Door and Window in a Wall
========================================
Door and window cut into a wall using IfcOpeningElement.
No shape_builder/mathutils needed.
Press F5 to run.
"""

import math
import numpy as np
import ifcopenshell.api.unit
import ifcopenshell.api.context
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.api.aggregate
import ifcopenshell.api.geometry
import ifcopenshell.api.material
import ifcopenshell.api.void

# --- Setup ---
project  = ifcopenshell.api.root.create_entity(model, ifc_class="IfcProject", name="Door Window Demo")
ifcopenshell.api.unit.assign_unit(model, length={"is_metric": True, "raw": "METRES"})
ctx  = ifcopenshell.api.context.add_context(model, context_type="Model")
body = ifcopenshell.api.context.add_context(model,
    context_type="Model", context_identifier="Body",
    target_view="MODEL_VIEW", parent=ctx)
site     = ifcopenshell.api.root.create_entity(model, ifc_class="IfcSite",     name="Site")
building = ifcopenshell.api.root.create_entity(model, ifc_class="IfcBuilding", name="Building")
storey   = ifcopenshell.api.root.create_entity(model, ifc_class="IfcBuildingStorey", name="GF")
for p, c in [(project,site),(site,building),(building,storey)]:
    ifcopenshell.api.aggregate.assign_object(model, relating_object=p, products=[c])

mat_masn = ifcopenshell.api.material.add_material(model, name="Masonry",  category="masonry")
mat_wood = ifcopenshell.api.material.add_material(model, name="Timber",   category="wood")
mat_alum = ifcopenshell.api.material.add_material(model, name="Aluminium",category="metal")


# ── Geometry helpers ───────────────────────────────────────────────────────

def z_axis():
    return model.create_entity("IfcDirection", DirectionRatios=(float(0), float(0), float(1)))

def x_axis():
    return model.create_entity("IfcDirection", DirectionRatios=(float(1), float(0), float(0)))

def pt(x, y, z):
    return model.create_entity("IfcCartesianPoint",
        Coordinates=(float(x), float(y), float(z)))

def axis3(x, y, z):
    return model.create_entity("IfcAxis2Placement3D",
        Location=pt(x, y, z), Axis=z_axis(), RefDirection=x_axis())

def rect_solid(xdim, ydim, depth, ox, oy, oz):
    prof = model.create_entity("IfcRectangleProfileDef",
               ProfileType="AREA", XDim=float(xdim), YDim=float(ydim))
    extr = model.create_entity("IfcExtrudedAreaSolid",
               SweptArea=prof, Position=axis3(ox, oy, oz),
               ExtrudedDirection=z_axis(), Depth=float(depth))
    rep  = model.create_entity("IfcShapeRepresentation",
               ContextOfItems=body,
               RepresentationIdentifier="Body",
               RepresentationType="SweptSolid", Items=[extr])
    return model.create_entity("IfcProductDefinitionShape", Representations=[rep])

def add_product(ifc_class, name, shape, mat, storey):
    e = ifcopenshell.api.root.create_entity(model, ifc_class=ifc_class, name=name)
    e.Representation = shape
    ifcopenshell.api.spatial.assign_container(model,
        relating_structure=storey, products=[e])
    ifcopenshell.api.geometry.edit_object_placement(model, product=e, matrix=np.eye(4))
    ifcopenshell.api.material.assign_material(model, products=[e], material=mat)
    return e


# ── Wall ──────────────────────────────────────────────────────────────────
WALL_L = 6.0; WALL_H = 3.0; WALL_T = 0.25

wall = add_product("IfcWall", "WALL-01",
    rect_solid(WALL_L, WALL_T, WALL_H, 0, 0, 0), mat_masn, storey)


# ── Door — IfcOpeningElement cuts hole, IfcDoor fills it ──────────────────
DOOR_W = 1.0; DOOR_H = 2.1
DOOR_X = 1.0  # position along wall

# 1. Opening void in wall
opening_door = ifcopenshell.api.root.create_entity(model,
    ifc_class="IfcOpeningElement", name="OPENING-DOOR")
opening_door.Representation = rect_solid(DOOR_W, WALL_T + 0.1, DOOR_H,
    DOOR_X, -0.05, 0)
ifcopenshell.api.geometry.edit_object_placement(model,
    product=opening_door, matrix=np.eye(4))

# 2. Void fills the wall
ifcopenshell.api.void.add_opening(model, opening=opening_door, element=wall)

# 3. Door element placed in the opening
door = ifcopenshell.api.root.create_entity(model, ifc_class="IfcDoor",
    name="DOOR-01", predefined_type="DOOR")
door.OverallWidth  = float(DOOR_W)
door.OverallHeight = float(DOOR_H)
door.Representation = rect_solid(DOOR_W - 0.05, WALL_T, DOOR_H - 0.05,
    DOOR_X + 0.025, 0, 0.025)
ifcopenshell.api.geometry.edit_object_placement(model,
    product=door, matrix=np.eye(4))
ifcopenshell.api.spatial.assign_container(model,
    relating_structure=storey, products=[door])
ifcopenshell.api.void.add_filling(model, opening=opening_door, element=door)
ifcopenshell.api.material.assign_material(model, products=[door], material=mat_wood)


# ── Window — same pattern ─────────────────────────────────────────────────
WIN_W = 1.2; WIN_H = 1.0; WIN_SILL = 1.0
WIN_X = 3.5   # position along wall

opening_win = ifcopenshell.api.root.create_entity(model,
    ifc_class="IfcOpeningElement", name="OPENING-WIN")
opening_win.Representation = rect_solid(WIN_W, WALL_T + 0.1, WIN_H,
    WIN_X, -0.05, WIN_SILL)
ifcopenshell.api.geometry.edit_object_placement(model,
    product=opening_win, matrix=np.eye(4))
ifcopenshell.api.void.add_opening(model, opening=opening_win, element=wall)

window = ifcopenshell.api.root.create_entity(model, ifc_class="IfcWindow",
    name="WIN-01", predefined_type="WINDOW")
window.OverallWidth  = float(WIN_W)
window.OverallHeight = float(WIN_H)
window.Representation = rect_solid(WIN_W - 0.05, 0.1, WIN_H - 0.05,
    WIN_X + 0.025, WALL_T/2 - 0.05, WIN_SILL + 0.025)
ifcopenshell.api.geometry.edit_object_placement(model,
    product=window, matrix=np.eye(4))
ifcopenshell.api.spatial.assign_container(model,
    relating_structure=storey, products=[window])
ifcopenshell.api.void.add_filling(model, opening=opening_win, element=window)
ifcopenshell.api.material.assign_material(model, products=[window], material=mat_alum)


print(f"Wall:   {WALL_L}m x {WALL_H}m x {WALL_T}m")
print(f"Door:   {DOOR_W}m x {DOOR_H}m  at X={DOOR_X}")
print(f"Window: {WIN_W}m x {WIN_H}m   at X={WIN_X}, sill={WIN_SILL}m")
