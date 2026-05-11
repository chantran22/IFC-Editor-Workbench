"""
Example 01 - Simple Wall
========================
5m x 3m x 0.2m wall. Press F5 to run.
"""

import numpy as np
import ifcopenshell.api.unit
import ifcopenshell.api.context
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.api.aggregate
import ifcopenshell.api.geometry
import ifcopenshell.api.pset
import ifcopenshell.api.material

# --- Project FIRST (required before assign_unit) ---
project  = ifcopenshell.api.root.create_entity(model, ifc_class="IfcProject", name="Demo")

# --- Units (needs IfcProject to exist) ---
ifcopenshell.api.unit.assign_unit(model, length={"is_metric": True, "raw": "METRES"})

# --- Geometry contexts ---
ctx  = ifcopenshell.api.context.add_context(model, context_type="Model")
body = ifcopenshell.api.context.add_context(model,
    context_type="Model", context_identifier="Body",
    target_view="MODEL_VIEW", parent=ctx)

# --- Spatial hierarchy ---
site     = ifcopenshell.api.root.create_entity(model, ifc_class="IfcSite",           name="Site")
building = ifcopenshell.api.root.create_entity(model, ifc_class="IfcBuilding",       name="Building")
storey   = ifcopenshell.api.root.create_entity(model, ifc_class="IfcBuildingStorey", name="L1")

for p, c in [(project,site),(site,building),(building,storey)]:
    ifcopenshell.api.aggregate.assign_object(model, relating_object=p, products=[c])

# --- Wall parameters ---
LENGTH = 5.0
HEIGHT = 3.0
THICK  = 0.2

# --- IFC geometry ---
z_dir   = model.create_entity("IfcDirection", DirectionRatios=(float(0.0), float(0.0), float(1.0)))
x_dir   = model.create_entity("IfcDirection", DirectionRatios=(float(1.0), float(0.0), float(0.0)))
origin  = model.create_entity("IfcCartesianPoint", Coordinates=(float(0.0), float(0.0), float(0.0)))
profile = model.create_entity("IfcRectangleProfileDef",
              ProfileType="AREA", XDim=LENGTH, YDim=THICK)
axis3   = model.create_entity("IfcAxis2Placement3D",
              Location=origin, Axis=z_dir, RefDirection=x_dir)
extr    = model.create_entity("IfcExtrudedAreaSolid",
              SweptArea=profile, Position=axis3,
              ExtrudedDirection=z_dir, Depth=HEIGHT)
rep     = model.create_entity("IfcShapeRepresentation",
              ContextOfItems=body,
              RepresentationIdentifier="Body",
              RepresentationType="SweptSolid",
              Items=[extr])
shape   = model.create_entity("IfcProductDefinitionShape", Representations=[rep])

# --- Wall entity ---
wall = ifcopenshell.api.root.create_entity(model, ifc_class="IfcWall", name="WALL-01")
wall.Representation = shape
ifcopenshell.api.spatial.assign_container(model, relating_structure=storey, products=[wall])
ifcopenshell.api.geometry.edit_object_placement(model, product=wall, matrix=np.eye(4))

# --- Pset & material ---
pset = ifcopenshell.api.pset.add_pset(model, product=wall, name="Pset_WallCommon")
ifcopenshell.api.pset.edit_pset(model, pset=pset, properties={
    "IsExternal": True, "LoadBearing": False, "FireRating": "REI60"})
mat = ifcopenshell.api.material.add_material(model, name="Concrete", category="concrete")
ifcopenshell.api.material.assign_material(model, products=[wall], material=mat)

print(f"Wall created: {LENGTH}m x {HEIGHT}m x {THICK}m")
