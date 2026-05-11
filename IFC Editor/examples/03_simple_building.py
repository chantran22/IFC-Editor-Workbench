"""
Example 03 - Simple Building Frame
====================================
Perimeter walls + corner columns + ground slab. No shape_builder/mathutils needed.
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

# --- Setup ---
project  = ifcopenshell.api.root.create_entity(model, ifc_class="IfcProject", name="Simple Frame")
ifcopenshell.api.unit.assign_unit(model, length={"is_metric": True, "raw": "METRES"})
ctx  = ifcopenshell.api.context.add_context(model, context_type="Model")
body = ifcopenshell.api.context.add_context(model,
    context_type="Model", context_identifier="Body",
    target_view="MODEL_VIEW", parent=ctx)
site     = ifcopenshell.api.root.create_entity(model, ifc_class="IfcSite",           name="Site")
building = ifcopenshell.api.root.create_entity(model, ifc_class="IfcBuilding",       name="Block A")
storey   = ifcopenshell.api.root.create_entity(model, ifc_class="IfcBuildingStorey", name="GF")
for p, c in [(project,site),(site,building),(building,storey)]:
    ifcopenshell.api.aggregate.assign_object(model, relating_object=p, products=[c])

mat_conc = ifcopenshell.api.material.add_material(model, name="Concrete", category="concrete")
mat_masn = ifcopenshell.api.material.add_material(model, name="Masonry",  category="masonry")

# --- Dimensions ---
W  = 10.0; L = 15.0; H = 3.5; WT = 0.25; ST = 0.2; CR = 0.225

# --- Geometry helpers ---
def make_extrusion(xdim, ydim, depth, ox, oy, oz, rotate_z=0.0):
    """Rectangle profile extruded along Z with optional Z rotation."""
    c, s   = math.cos(rotate_z), math.sin(rotate_z)
    z_dir  = model.create_entity("IfcDirection", DirectionRatios=(float(0.0), float(0.0), float(1.0)))
    x_dir  = model.create_entity("IfcDirection", DirectionRatios=(float(c), float(s), float(0.0)))
    origin = model.create_entity("IfcCartesianPoint", Coordinates=(float(ox), float(oy), float(oz)))
    prof   = model.create_entity("IfcRectangleProfileDef",
                 ProfileType="AREA", XDim=xdim, YDim=ydim)
    ax3    = model.create_entity("IfcAxis2Placement3D",
                 Location=origin, Axis=z_dir, RefDirection=x_dir)
    extr   = model.create_entity("IfcExtrudedAreaSolid",
                 SweptArea=prof, Position=ax3,
                 ExtrudedDirection=z_dir, Depth=depth)
    rep    = model.create_entity("IfcShapeRepresentation",
                 ContextOfItems=body,
                 RepresentationIdentifier="Body",
                 RepresentationType="SweptSolid", Items=[extr])
    return model.create_entity("IfcProductDefinitionShape", Representations=[rep])

def make_circle_extrusion(radius, depth, ox, oy, oz):
    z_dir  = model.create_entity("IfcDirection", DirectionRatios=(float(0.0), float(0.0), float(1.0)))
    ax2_2d = model.create_entity("IfcAxis2Placement2D",
                 Location=model.create_entity("IfcCartesianPoint", Coordinates=(float(0.0), float(0.0))))
    prof   = model.create_entity("IfcCircleProfileDef",
                 ProfileType="AREA", Radius=radius, Position=ax2_2d)
    origin = model.create_entity("IfcCartesianPoint", Coordinates=(float(ox), float(oy), float(oz)))
    ax3    = model.create_entity("IfcAxis2Placement3D", Location=origin, Axis=z_dir)
    extr   = model.create_entity("IfcExtrudedAreaSolid",
                 SweptArea=prof, Position=ax3,
                 ExtrudedDirection=z_dir, Depth=depth)
    rep    = model.create_entity("IfcShapeRepresentation",
                 ContextOfItems=body,
                 RepresentationIdentifier="Body",
                 RepresentationType="SweptSolid", Items=[extr])
    return model.create_entity("IfcProductDefinitionShape", Representations=[rep])

def add_element(ifc_class, name, shape, mat):
    e = ifcopenshell.api.root.create_entity(model, ifc_class=ifc_class, name=name)
    e.Representation = shape
    ifcopenshell.api.spatial.assign_container(model, relating_structure=storey, products=[e])
    ifcopenshell.api.geometry.edit_object_placement(model, product=e, matrix=np.eye(4))
    ifcopenshell.api.material.assign_material(model, products=[e], material=mat)
    return e

# --- Walls (4 perimeter) ---
add_element("IfcWall", "WALL-S",  make_extrusion(W, WT, H, 0,   0,   0), mat_masn)
add_element("IfcWall", "WALL-N",  make_extrusion(W, WT, H, 0,   L-WT,0), mat_masn)
add_element("IfcWall", "WALL-W",  make_extrusion(L, WT, H, 0,   0,   0, math.pi/2), mat_masn)
add_element("IfcWall", "WALL-E",  make_extrusion(L, WT, H, W-WT,0,   0, math.pi/2), mat_masn)

# --- Corner columns ---
for tag, cx, cy in [("COL-SW",0,0),("COL-SE",W,0),("COL-NW",0,L),("COL-NE",W,L)]:
    add_element("IfcColumn", tag, make_circle_extrusion(CR, H, cx, cy, 0), mat_conc)

# --- Ground slab ---
add_element("IfcSlab", "SLAB-GF", make_extrusion(W, L, ST, 0, 0, -ST), mat_conc)

print(f"Building frame: {W}m x {L}m x {H}m | 4 walls, 4 columns, 1 slab")
