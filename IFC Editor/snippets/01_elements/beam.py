"""
Beam - IfcBeam with rectangular profile along X axis.
Requires: storey, body context already defined.
Edit: span, width, depth, position.
"""

import numpy as np
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.api.geometry

# --- Parameters ---
SPAN   = 6.0    # length along X
WIDTH  = 0.3    # beam width (Y)
DEPTH  = 0.5    # beam depth (Z)
X      = 0.0
Y      = 0.0
Z      = 3.0    # elevation (top of column)

# Beam extrudes along X — so profile is in YZ plane
# Use IfcIShapeProfileDef for I-beam or IfcRectangleProfileDef for RC
profile = model.create_entity("IfcRectangleProfileDef",
              ProfileType="AREA", XDim=WIDTH, YDim=DEPTH)

# Extrude along X: axis pointing X, extrude direction X
x_dir   = model.create_entity("IfcDirection", DirectionRatios=(float(1.0), float(0.0), float(0.0)))
z_dir   = model.create_entity("IfcDirection", DirectionRatios=(float(0.0), float(0.0), float(1.0)))
origin  = model.create_entity("IfcCartesianPoint", Coordinates=(float(X), float(Y), float(Z)))
axis3   = model.create_entity("IfcAxis2Placement3D",
              Location=origin, Axis=x_dir, RefDirection=z_dir)
extr    = model.create_entity("IfcExtrudedAreaSolid",
              SweptArea=profile, Position=axis3,
              ExtrudedDirection=x_dir, Depth=SPAN)
rep     = model.create_entity("IfcShapeRepresentation",
              ContextOfItems=body,
              RepresentationIdentifier="Body",
              RepresentationType="SweptSolid",
              Items=[extr])
shape   = model.create_entity("IfcProductDefinitionShape", Representations=[rep])

beam = ifcopenshell.api.root.create_entity(model, ifc_class="IfcBeam", name="BM-01")
beam.Representation = shape
ifcopenshell.api.spatial.assign_container(model, relating_structure=storey, products=[beam])
ifcopenshell.api.geometry.edit_object_placement(model, product=beam, matrix=np.eye(4))
