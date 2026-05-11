# -*- coding: utf-8 -*-
"""
ifc_helpers.py — Simple IFC geometry commands for IFC Code Editor WB.

Design goal: beginner-friendly API similar to CadQuery/Part WB.
User writes:
    ctx = IFCContext(model)
    wall   = ctx.make_wall(length=5, height=3, thickness=0.2)
    col    = ctx.make_column(diameter=0.4, height=3.5, x=6, y=0)
    cols   = ctx.array(col, dx=6, dy=0, nx=4, ny=3)
    ctx.export("output.ifc")

No knowledge of IFC schema required.
"""

import numpy as np
import ifcopenshell
import ifcopenshell.api.unit
import ifcopenshell.api.context
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.api.aggregate
import ifcopenshell.api.geometry
import ifcopenshell.api.material
import ifcopenshell.api.pset


class IFCContext:
    """
    Main entry point. Wraps an ifcopenshell.file with simple geometry commands.

    Usage:
        ctx = IFCContext(model)          # model from sandbox namespace
        ctx.setup("My Project")         # creates project/site/building/storey
        wall = ctx.make_wall(5, 3, 0.2)
    """

    def __init__(self, model):
        self.model    = model
        self.project  = None
        self.site     = None
        self.building = None
        self.storey   = None
        self.body     = None
        self._elements = []

    # ── Setup ────────────────────────────────────────────────────────────

    def setup(self, project_name="My Project", site_name="Site",
              building_name="Building", storey_name="Level 1"):
        """
        Create project/site/building/storey hierarchy + units + geometry context.
        Call this once at the start of every script.
        """
        m = self.model

        self.project  = ifcopenshell.api.root.create_entity(m,
            ifc_class="IfcProject", name=project_name)
        ifcopenshell.api.unit.assign_unit(m, length={"is_metric":True,"raw":"METRES"})

        ctx_geom   = ifcopenshell.api.context.add_context(m, context_type="Model")
        self.body  = ifcopenshell.api.context.add_context(m,
            context_type="Model", context_identifier="Body",
            target_view="MODEL_VIEW", parent=ctx_geom)

        self.site     = ifcopenshell.api.root.create_entity(m, ifc_class="IfcSite",     name=site_name)
        self.building = ifcopenshell.api.root.create_entity(m, ifc_class="IfcBuilding", name=building_name)
        self.storey   = ifcopenshell.api.root.create_entity(m,
            ifc_class="IfcBuildingStorey", name=storey_name)

        ifcopenshell.api.aggregate.assign_object(m,
            relating_object=self.project, products=[self.site])
        ifcopenshell.api.aggregate.assign_object(m,
            relating_object=self.site, products=[self.building])
        ifcopenshell.api.aggregate.assign_object(m,
            relating_object=self.building, products=[self.storey])

        # Verify body context was created
        if self.body is None:
            raise RuntimeError("Failed to create geometry context in ctx.setup()")

        return self

    def add_storey(self, name, elevation=0.0):
        """Add an extra building storey."""
        s = ifcopenshell.api.root.create_entity(self.model,
            ifc_class="IfcBuildingStorey", name=name)
        ifcopenshell.api.aggregate.assign_object(self.model,
            relating_object=self.building, products=[s])
        return s

    # ── Internal geometry builders ────────────────────────────────────────

    def _z(self): return self.model.create_entity("IfcDirection",
        DirectionRatios=(float(0), float(0), float(1)))

    def _x(self): return self.model.create_entity("IfcDirection",
        DirectionRatios=(float(1), float(0), float(0)))

    def _pt(self, x, y, z): return self.model.create_entity("IfcCartesianPoint",
        Coordinates=(float(x), float(y), float(z)))

    def _ax3(self, x, y, z, angle_z=0.0):
        import math
        c, s = math.cos(angle_z), math.sin(angle_z)
        ref = self.model.create_entity("IfcDirection",
            DirectionRatios=(float(c), float(s), float(0)))
        return self.model.create_entity("IfcAxis2Placement3D",
            Location=self._pt(x,y,z), Axis=self._z(), RefDirection=ref)

    def _rect_solid(self, xdim, ydim, depth, ox, oy, oz, angle_z=0.0):
        prof = self.model.create_entity("IfcRectangleProfileDef",
            ProfileType="AREA", XDim=float(xdim), YDim=float(ydim))
        extr = self.model.create_entity("IfcExtrudedAreaSolid",
            SweptArea=prof, Position=self._ax3(ox,oy,oz,angle_z),
            ExtrudedDirection=self._z(), Depth=float(depth))
        rep = self.model.create_entity("IfcShapeRepresentation",
            ContextOfItems=self.body,
            RepresentationIdentifier="Body",
            RepresentationType="SweptSolid", Items=[extr])
        return self.model.create_entity("IfcProductDefinitionShape", Representations=[rep])

    def _circle_solid(self, radius, depth, ox, oy, oz):
        ax2d = self.model.create_entity("IfcAxis2Placement2D",
            Location=self.model.create_entity("IfcCartesianPoint",
                Coordinates=(float(0), float(0))))
        prof = self.model.create_entity("IfcCircleProfileDef",
            ProfileType="AREA", Radius=float(radius), Position=ax2d)
        extr = self.model.create_entity("IfcExtrudedAreaSolid",
            SweptArea=prof, Position=self._ax3(ox,oy,oz),
            ExtrudedDirection=self._z(), Depth=float(depth))
        rep = self.model.create_entity("IfcShapeRepresentation",
            ContextOfItems=self.body,
            RepresentationIdentifier="Body",
            RepresentationType="SweptSolid", Items=[extr])
        return self.model.create_entity("IfcProductDefinitionShape", Representations=[rep])

    def _place(self, product, x=0, y=0, z=0, angle_z=0.0):
        import math
        c, s = math.cos(angle_z), math.sin(angle_z)
        m = np.array([
            [c,  -s,  0,  float(x)],
            [s,   c,  0,  float(y)],
            [0,   0,  1,  float(z)],
            [0,   0,  0,  1.0],
        ])
        ifcopenshell.api.geometry.edit_object_placement(self.model,
            product=product, matrix=m)

    def _add_to_storey(self, product, storey=None):
        storey = storey or self.storey
        ifcopenshell.api.spatial.assign_container(self.model,
            relating_structure=storey, products=[product])

    def _make_material(self, name, category="concrete"):
        return ifcopenshell.api.material.add_material(self.model,
            name=name, category=category)

    def _assign_mat(self, product, material):
        if material:
            ifcopenshell.api.material.assign_material(self.model,
                products=[product], material=material)

    # ── Public element creation ───────────────────────────────────────────

    def make_wall(self, length, height, thickness=0.2,
                  x=0, y=0, z=0, angle_z=0.0,
                  name="Wall", material=None, storey=None):
        """
        Create a wall.
        length, height, thickness — metres
        x, y, z — position of wall start point
        angle_z — rotation in radians (0=along X axis)
        """
        e = ifcopenshell.api.root.create_entity(self.model,
            ifc_class="IfcWall", name=name)
        e.Representation = self._rect_solid(length, thickness, height,
            x, y, z, angle_z)
        self._place(e, x, y, z, angle_z)
        self._add_to_storey(e, storey)
        self._assign_mat(e, material)
        self._elements.append(e)
        return e

    def make_column(self, height, diameter=None, width=None, depth=None,
                    x=0, y=0, z=0,
                    name="Column", material=None, storey=None):
        """
        Create a column.
        diameter — circular section (metres)
        width + depth — rectangular section (metres)
        """
        e = ifcopenshell.api.root.create_entity(self.model,
            ifc_class="IfcColumn", name=name)
        if diameter:
            e.Representation = self._circle_solid(diameter/2, height, x, y, z)
        else:
            w = width or 0.4
            d = depth or width or 0.4
            e.Representation = self._rect_solid(w, d, height, x, y, z)
        self._place(e, x, y, z)
        self._add_to_storey(e, storey)
        self._assign_mat(e, material)
        self._elements.append(e)
        return e

    def make_beam(self, span, width=0.3, depth=0.5,
                  x=0, y=0, z=0, angle_z=0.0,
                  name="Beam", material=None, storey=None):
        """Create a rectangular beam along X direction."""
        import math
        e = ifcopenshell.api.root.create_entity(self.model,
            ifc_class="IfcBeam", name=name)
        # Beam extrudes along its local X — profile in YZ plane
        prof = self.model.create_entity("IfcRectangleProfileDef",
            ProfileType="AREA", XDim=float(width), YDim=float(depth))
        # Extrude direction = local X
        beam_dir = self.model.create_entity("IfcDirection",
            DirectionRatios=(float(1), float(0), float(0)))
        c, s = math.cos(angle_z), math.sin(angle_z)
        z_ref = self.model.create_entity("IfcDirection",
            DirectionRatios=(float(0), float(0), float(1)))
        ax3 = self.model.create_entity("IfcAxis2Placement3D",
            Location=self._pt(x, y, z),
            Axis=beam_dir,
            RefDirection=z_ref)
        extr = self.model.create_entity("IfcExtrudedAreaSolid",
            SweptArea=prof, Position=ax3,
            ExtrudedDirection=beam_dir, Depth=float(span))
        rep = self.model.create_entity("IfcShapeRepresentation",
            ContextOfItems=self.body,
            RepresentationIdentifier="Body",
            RepresentationType="SweptSolid", Items=[extr])
        e.Representation = self.model.create_entity(
            "IfcProductDefinitionShape", Representations=[rep])
        self._place(e, x, y, z, angle_z)
        self._add_to_storey(e, storey)
        self._assign_mat(e, material)
        self._elements.append(e)
        return e

    def make_slab(self, width, length, thickness=0.2,
                  x=0, y=0, z=0,
                  name="Slab", material=None, storey=None):
        """Create a flat slab."""
        e = ifcopenshell.api.root.create_entity(self.model,
            ifc_class="IfcSlab", name=name)
        e.Representation = self._rect_solid(width, length, thickness, x, y, z)
        self._place(e, x, y, z)
        self._add_to_storey(e, storey)
        self._assign_mat(e, material)
        self._elements.append(e)
        return e

    def make_footing(self, width, length, depth=0.5,
                     x=0, y=0, z=None,
                     name="Footing", material=None, storey=None):
        """Create a pad footing (below grade)."""
        if z is None:
            z = -depth
        e = ifcopenshell.api.root.create_entity(self.model,
            ifc_class="IfcFooting", name=name, predefined_type="PAD_FOOTING")
        e.Representation = self._rect_solid(width, length, depth, x, y, z)
        self._place(e, x, y, z)
        self._add_to_storey(e, storey)
        self._assign_mat(e, material)
        self._elements.append(e)
        return e

    # ── Array / copy ──────────────────────────────────────────────────────

    def array(self, template_func, nx=1, ny=1, nz=1,
              dx=0, dy=0, dz=0):
        """
        Create a grid array by calling template_func(x, y, z) for each position.

        Example:
            cols = ctx.array(
                lambda x,y,z: ctx.make_column(height=4, diameter=0.4,
                                              x=x, y=y, z=z),
                nx=4, ny=3, dx=6, dy=7)
        """
        elements = []
        for iz in range(nz):
            for iy in range(ny):
                for ix in range(nx):
                    e = template_func(ix * dx, iy * dy, iz * dz)
                    elements.append(e)
        return elements

    # ── Properties ────────────────────────────────────────────────────────

    def add_pset(self, element, pset_name, **properties):
        """
        Add a property set to an element.

        Example:
            ctx.add_pset(wall, "Pset_WallCommon",
                IsExternal=True, FireRating="REI60")
        """
        pset = ifcopenshell.api.pset.add_pset(self.model,
            product=element, name=pset_name)
        ifcopenshell.api.pset.edit_pset(self.model,
            pset=pset, properties=properties)
        return pset

    # ── Materials ─────────────────────────────────────────────────────────

    def material(self, name, category="concrete"):
        """Create a material. category: concrete / masonry / steel / wood / glass"""
        return self._make_material(name, category)

    # ── Export ────────────────────────────────────────────────────────────

    def export(self, filepath):
        """Write IFC file directly. Same as Export IFC button."""
        self.model.write(filepath)
        print(f"Exported: {filepath}")

    def element_count(self):
        return len(self._elements)