# -*- coding: utf-8 -*-
"""
ifc_tools.py — Geometry modeling tools for IFC Code Editor WB.

Similar to Part WB / CadQuery operations but outputs IFC geometry.
All functions work without mathutils or bpy.

Rotation tools:
    rotate(element, angle_z)            — rotate around Z (vertical axis)
    rotate_z(element, angle)            — same as rotate()
    rotate_x(element, angle)            — tilt around X (for ramps, slopes)
    rotate_y(element, angle)            — lean around Y (for inclined columns)
    rotate_axis(element, axis, angle)   — rotate around any arbitrary axis

Extrude tools:
    extrude(profile_pts, depth)         — extrude along Z axis (default)
    extrude_along_x(profile_pts, len)  — extrude along X axis (beams)
    extrude_along_y(profile_pts, len)  — extrude along Y axis (purlins)
    extrude_along_dir(profile, dir, len)— extrude along any direction vector

Sweep / Loft:
    sweep(profile_pts, path_pts)        — sweep profile along 3D path
    loft(profiles_with_z)              — loft between profiles at Z heights

Boolean operations:
    subtract(base, tool)               — base MINUS tool (cut hole)
    union(a, b)                        — a UNION b (merge solids)
    intersect(a, b)                    — keep only common volume

Transform:
    translate(element, dx, dy, dz)     — move, preserves rotation
    rotate / rotate_x / rotate_y / rotate_z / rotate_axis
    copy(element, dx, dy, dz)         — duplicate to new position
    mirror_x / mirror_y               — mirror about axis

Array:
    array(func, nx, ny, nz, dx, dy, dz)    — rectangular grid
    polar_array(func, count, radius)        — circular array

Profiles:
    make_profile_rect(w, h)            — rectangle
    make_profile_L(w, h, t)           — L-section
    make_profile_I(w, h, tw, tf)      — I-beam
    make_profile_C(w, h, t)           — C-channel
    make_profile_circle(r, segments)   — circle
"""

import math
import numpy as np
import FreeCAD
import ifcopenshell
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.api.geometry
import ifcopenshell.api.material


class IFCTools:
    """
    Geometry modeling tools. Attach to an IFCContext:
        tools = IFCTools(ctx)
        wall  = tools.extrude(tools.make_profile_rect(5, 0.2), depth=3)
    """

    def __init__(self, ctx):
        self.ctx   = ctx
        self.model = ctx.model

    # ── Internal helpers ─────────────────────────────────────────────────

    def _z(self):
        return self.model.create_entity("IfcDirection",
            DirectionRatios=(float(0), float(0), float(1)))

    def _dir(self, x, y, z):
        return self.model.create_entity("IfcDirection",
            DirectionRatios=(float(x), float(y), float(z)))

    def _pt3(self, x, y, z):
        return self.model.create_entity("IfcCartesianPoint",
            Coordinates=(float(x), float(y), float(z)))

    def _pt2(self, x, y):
        return self.model.create_entity("IfcCartesianPoint",
            Coordinates=(float(x), float(y)))

    def _ax3(self, x=0, y=0, z=0, angle_z=0.0):
        c, s = math.cos(angle_z), math.sin(angle_z)
        return self.model.create_entity("IfcAxis2Placement3D",
            Location=self._pt3(x, y, z),
            Axis=self._z(),
            RefDirection=self._dir(c, s, 0))

    def _poly_profile(self, points_2d):
        """Create IfcArbitraryClosedProfileDef from list of (x,y) points."""
        ifc_pts = [self._pt2(p[0], p[1]) for p in points_2d]
        # Close the polyline
        if points_2d[0] != points_2d[-1]:
            ifc_pts.append(ifc_pts[0])
        polyline = self.model.create_entity("IfcPolyline", Points=ifc_pts)
        return self.model.create_entity("IfcArbitraryClosedProfileDef",
            ProfileType="AREA", OuterCurve=polyline)

    def _make_rep(self, items, rep_type="SweptSolid"):
        body = self.ctx.body
        if body is None:
            raise RuntimeError(
                "No geometry context — ctx.body is None.\n"
                "Make sure ctx.setup() is called BEFORE tools.extrude().")
        rep = self.model.create_entity("IfcShapeRepresentation",
            ContextOfItems=body,
            RepresentationIdentifier="Body",
            RepresentationType=rep_type,
            Items=items)
        return self.model.create_entity("IfcProductDefinitionShape",
            Representations=[rep])

    def _place_matrix(self, product, matrix):
        ifcopenshell.api.geometry.edit_object_placement(self.model,
            product=product, matrix=matrix)

    def _matrix(self, x=0, y=0, z=0, angle_z=0.0):
        c, s = math.cos(angle_z), math.sin(angle_z)
        return np.array([
            [c,  -s,  0, float(x)],
            [s,   c,  0, float(y)],
            [0,   0,  1, float(z)],
            [0,   0,  0, 1.0],
        ])

    def _add_to_model(self, ifc_class, name, shape, storey=None, material=None):
        e = ifcopenshell.api.root.create_entity(self.model,
            ifc_class=ifc_class, name=name)
        e.Representation = shape
        target = storey or self.ctx.storey
        if target is None:
            raise RuntimeError(
                "No storey found. Call ctx.setup() before using tools.*")
        ifcopenshell.api.spatial.assign_container(self.model,
            relating_structure=target, products=[e])
        if material:
            ifcopenshell.api.material.assign_material(self.model,
                products=[e], material=material)
        return e

    # ── Profile generators ───────────────────────────────────────────────

    def make_profile_rect(self, width, height):
        """Rectangle profile: [(x,y), ...] — width along X, height along Y."""
        w, h = width / 2, height / 2
        return [(-w, -h), (w, -h), (w, h), (-w, h)]

    def make_profile_L(self, width, height, thickness):
        """L-section profile."""
        t = thickness
        return [(0, 0), (width, 0), (width, t), (t, t), (t, height), (0, height)]

    def make_profile_I(self, width, height, web_thickness, flange_thickness):
        """I-beam profile."""
        w, h  = width / 2, height / 2
        wt, ft = web_thickness / 2, flange_thickness
        return [
            (-w,  -h),  (w,  -h),  (w,  -h+ft),
            (wt,  -h+ft),(wt, h-ft),(w,  h-ft),
            (w,   h),   (-w, h),   (-w, h-ft),
            (-wt, h-ft),(-wt,-h+ft),(-w,-h+ft),
        ]

    def make_profile_C(self, width, height, thickness):
        """C-channel profile."""
        t = thickness
        return [
            (0, 0), (width, 0), (width, t),
            (t, t), (t, height - t), (width, height - t),
            (width, height), (0, height),
        ]

    def make_profile_circle(self, radius, segments=16):
        """Circle approximated as polygon."""
        return [
            (radius * math.cos(2*math.pi*i/segments),
             radius * math.sin(2*math.pi*i/segments))
            for i in range(segments)
        ]

    # ── Core operations ──────────────────────────────────────────────────

    def extrude(self, profile_points, depth,
                x=0, y=0, z=0, angle_z=0.0,
                ifc_class="IfcBuildingElementProxy",
                name="Extruded", material=None, storey=None):
        """
        Extrude a 2D profile (list of (x,y) points) along Z axis.

        Example — L-beam 3m long:
            profile = tools.make_profile_L(0.1, 0.15, 0.01)
            beam = tools.extrude(profile, depth=3.0, ifc_class="IfcBeam")
        """
        prof = self._poly_profile(profile_points)
        extr = self.model.create_entity("IfcExtrudedAreaSolid",
            SweptArea=prof,
            Position=self._ax3(x, y, z, angle_z),
            ExtrudedDirection=self._z(),
            Depth=float(depth))
        shape = self._make_rep([extr])
        e = self._add_to_model(ifc_class, name, shape, storey, material)
        self._place_matrix(e, self._matrix(x, y, z, angle_z))
        return e

    def sweep(self, profile_points, path_points,
              ifc_class="IfcBuildingElementProxy",
              name="Swept", material=None, storey=None):
        """
        Sweep a 2D profile along a 3D polyline path.

        Example — curved handrail:
            profile = tools.make_profile_circle(radius=0.025)
            path = [(0,0,0),(2,0,0),(2,2,0),(2,2,3)]
            rail = tools.sweep(profile, path, ifc_class="IfcRailing")
        """
        # Profile
        prof = self._poly_profile(profile_points)

        # Path as IfcPolyline
        ifc_path_pts = [self._pt3(p[0], p[1], p[2]) for p in path_points]
        path_polyline = self.model.create_entity("IfcPolyline",
            Points=ifc_path_pts)
        composite = self.model.create_entity(
            "IfcCompositeCurve",
            Segments=[],
            SelfIntersect=False)
        # Use IfcFixedReferenceSweptAreaSolid (IFC4)
        try:
            solid = self.model.create_entity(
                "IfcFixedReferenceSweptAreaSolid",
                SweptArea=prof,
                Position=self._ax3(0, 0, 0),
                Directrix=path_polyline,
                FixedReference=self._dir(0, 0, 1))
        except Exception:
            # Fallback: simple extrude along first segment
            dx = path_points[-1][0] - path_points[0][0]
            dy = path_points[-1][1] - path_points[0][1]
            dz = path_points[-1][2] - path_points[0][2]
            length = math.sqrt(dx**2 + dy**2 + dz**2)
            return self.extrude(profile_points, length,
                x=path_points[0][0], y=path_points[0][1], z=path_points[0][2],
                ifc_class=ifc_class, name=name, material=material, storey=storey)

        shape = self._make_rep([solid])
        e = self._add_to_model(ifc_class, name, shape, storey, material)
        self._place_matrix(e, np.eye(4))
        return e

    def loft(self, profiles_with_z,
             ifc_class="IfcBuildingElementProxy",
             name="Lofted", material=None, storey=None):
        """
        Approximate loft between profiles at different Z heights.
        profiles_with_z: list of (z_height, profile_points)

        Example — tapered column (square at base, circle at top):
            profiles = [
                (0.0,  tools.make_profile_rect(0.5, 0.5)),
                (4.0,  tools.make_profile_circle(0.2)),
            ]
            col = tools.loft(profiles, ifc_class="IfcColumn")

        Note: IFC4 loft uses IfcSectionedSolidHorizontal.
        Falls back to extrude of first profile if schema doesn't support it.
        """
        try:
            cross_sections = []
            positions = []
            for z_height, pts in profiles_with_z:
                cross_sections.append(self._poly_profile(pts))
                positions.append(self.model.create_entity(
                    "IfcAxis2PlacementLinear",
                    Location=self._pt3(0, 0, z_height)))

            # IfcSectionedSolidHorizontal — IFC4 ADD2
            directrix_pts = [self._pt3(0, 0, z) for z, _ in profiles_with_z]
            directrix = self.model.create_entity("IfcPolyline",
                Points=directrix_pts)
            solid = self.model.create_entity("IfcSectionedSolidHorizontal",
                Directrix=directrix,
                CrossSections=cross_sections,
                CrossSectionPositions=positions)
            shape = self._make_rep([solid])

        except Exception:
            # Fallback: extrude first profile full height
            z0, pts0 = profiles_with_z[0]
            z1, _    = profiles_with_z[-1]
            return self.extrude(pts0, depth=z1 - z0, z=z0,
                ifc_class=ifc_class, name=name,
                material=material, storey=storey)

        e = self._add_to_model(ifc_class, name, shape, storey, material)
        self._place_matrix(e, np.eye(4))
        return e

    # ── Transform operations ─────────────────────────────────────────────

    def _read_matrix(self, element):
        """Read current placement as 4x4 numpy matrix."""
        try:
            import ifcopenshell.util.placement
            return ifcopenshell.util.placement.get_local_placement(
                element.ObjectPlacement)
        except Exception:
            return np.eye(4)

    def translate(self, element, dx=0, dy=0, dz=0):
        """
        Move element by (dx, dy, dz) — preserves existing rotation.

        Example:
            tools.translate(wall, dx=5, dy=0)
        """
        m = self._read_matrix(element).copy()
        m[0, 3] += float(dx)
        m[1, 3] += float(dy)
        m[2, 3] += float(dz)
        self._place_matrix(element, m)
        return element

    def rotate(self, element, angle_z, cx=0, cy=0):
        """
        Rotate element around Z axis — preserves existing translation.
        angle_z in radians. cx, cy = centre of rotation.

        Example:
            tools.rotate(wall, math.pi/2)        # 90 degrees around Z
            tools.rotate(wall, math.pi/2, cx=5)  # rotate around x=5
        """
        return self.rotate_z(element, angle_z, cx=cx, cy=cy)

    def rotate_z(self, element, angle, cx=0, cy=0):
        """
        Rotate element around Z axis (vertical).
        angle in radians. cx, cy = centre of rotation.

        Example:
            tools.rotate_z(wall, math.pi/2)       # 90deg vertical rotation
        """
        m = self._read_matrix(element).copy()
        x, y, z = m[0,3], m[1,3], m[2,3]
        c, s = math.cos(angle), math.sin(angle)
        rot = np.array([[c,-s,0,0],[s,c,0,0],[0,0,1,0],[0,0,0,1]])
        new_m = rot @ m
        px, py = x - cx, y - cy
        new_m[0,3] = c*px - s*py + cx
        new_m[1,3] = s*px + c*py + cy
        new_m[2,3] = z
        self._place_matrix(element, new_m)
        return element

    def rotate_x(self, element, angle, cy=0, cz=0):
        """
        Rotate element around X axis.
        angle in radians. cy, cz = centre of rotation.

        Useful for: tilting slabs, ramps, inclined elements.

        Example:
            tools.rotate_x(slab, math.radians(15))   # 15deg slope
        """
        m = self._read_matrix(element).copy()
        x, y, z = m[0,3], m[1,3], m[2,3]
        c, s = math.cos(angle), math.sin(angle)
        rot = np.array([[1,0,0,0],[0,c,-s,0],[0,s,c,0],[0,0,0,1]])
        new_m = rot @ m
        py, pz = y - cy, z - cz
        new_m[0,3] = x
        new_m[1,3] =  c*py - s*pz + cy
        new_m[2,3] =  s*py + c*pz + cz
        self._place_matrix(element, new_m)
        return element

    def rotate_y(self, element, angle, cx=0, cz=0):
        """
        Rotate element around Y axis.
        angle in radians. cx, cz = centre of rotation.

        Useful for: rotating beams to horizontal, inclined columns.

        Example:
            tools.rotate_y(col, math.radians(30))    # 30deg lean
        """
        m = self._read_matrix(element).copy()
        x, y, z = m[0,3], m[1,3], m[2,3]
        c, s = math.cos(angle), math.sin(angle)
        rot = np.array([[c,0,s,0],[0,1,0,0],[-s,0,c,0],[0,0,0,1]])
        new_m = rot @ m
        px, pz = x - cx, z - cz
        new_m[0,3] =  c*px + s*pz + cx
        new_m[1,3] =  y
        new_m[2,3] = -s*px + c*pz + cz
        self._place_matrix(element, new_m)
        return element

    def rotate_axis(self, element, axis, angle, origin=(0,0,0)):
        """
        Rotate element around an arbitrary axis vector.
        Uses Rodrigues' rotation formula.

        axis   — (x,y,z) direction vector (will be normalised)
        angle  — radians
        origin — (x,y,z) point to rotate around

        Example:
            # Rotate around diagonal axis 45 degrees
            tools.rotate_axis(beam, axis=(1,1,0), angle=math.pi/4)

            # Lean a column 10deg toward northeast
            tools.rotate_axis(col, axis=(1,-1,0), angle=math.radians(10))
        """
        ax = np.array(axis, dtype=float)
        ax = ax / np.linalg.norm(ax)   # normalise
        ux, uy, uz = ax
        c, s = math.cos(angle), math.sin(angle)
        t = 1 - c
        # Rodrigues rotation matrix
        rot = np.array([
            [t*ux*ux + c,    t*ux*uy - s*uz, t*ux*uz + s*uy, 0],
            [t*ux*uy + s*uz, t*uy*uy + c,    t*uy*uz - s*ux, 0],
            [t*ux*uz - s*uy, t*uy*uz + s*ux, t*uz*uz + c,    0],
            [0,              0,              0,               1],
        ])
        m = self._read_matrix(element).copy()
        ox, oy, oz = origin
        # Translate to origin, rotate, translate back
        pos = np.array([m[0,3]-ox, m[1,3]-oy, m[2,3]-oz, 1.0])
        new_pos = rot @ pos
        new_m = rot @ m
        new_m[0,3] = new_pos[0] + ox
        new_m[1,3] = new_pos[1] + oy
        new_m[2,3] = new_pos[2] + oz
        self._place_matrix(element, new_m)
        return element

    # ── Profile rotation helpers (for sweep/extrude direction) ────────────

    def extrude_along_x(self, profile_points, length,
                        x=0, y=0, z=0,
                        ifc_class="IfcBuildingElementProxy",
                        name="Extruded", material=None, storey=None):
        """
        Extrude profile along X axis (horizontal beam direction).

        Example:
            profile = tools.make_profile_I(0.2, 0.3, 0.01, 0.015)
            beam = tools.extrude_along_x(profile, length=6,
                       x=0, y=0, z=3, ifc_class="IfcBeam")
        """
        prof = self._poly_profile(profile_points)
        x_dir = self._dir(1, 0, 0)
        z_ref = self._dir(0, 0, 1)
        ax3   = self.model.create_entity("IfcAxis2Placement3D",
                    Location=self._pt3(x,y,z), Axis=x_dir, RefDirection=z_ref)
        extr  = self.model.create_entity("IfcExtrudedAreaSolid",
                    SweptArea=prof, Position=ax3,
                    ExtrudedDirection=x_dir, Depth=float(length))
        shape = self._make_rep([extr])
        e = self._add_to_model(ifc_class, name, shape, storey, material)
        self._place_matrix(e, self._matrix(x, y, z))
        return e

    def extrude_along_y(self, profile_points, length,
                        x=0, y=0, z=0,
                        ifc_class="IfcBuildingElementProxy",
                        name="Extruded", material=None, storey=None):
        """
        Extrude profile along Y axis.

        Example:
            profile = tools.make_profile_rect(0.3, 0.5)
            purlin = tools.extrude_along_y(profile, length=8,
                         x=0, y=0, z=5, ifc_class="IfcBeam")
        """
        prof  = self._poly_profile(profile_points)
        y_dir = self._dir(0, 1, 0)
        x_ref = self._dir(1, 0, 0)
        ax3   = self.model.create_entity("IfcAxis2Placement3D",
                    Location=self._pt3(x,y,z), Axis=y_dir, RefDirection=x_ref)
        extr  = self.model.create_entity("IfcExtrudedAreaSolid",
                    SweptArea=prof, Position=ax3,
                    ExtrudedDirection=y_dir, Depth=float(length))
        shape = self._make_rep([extr])
        e = self._add_to_model(ifc_class, name, shape, storey, material)
        self._place_matrix(e, self._matrix(x, y, z))
        return e

    def extrude_along_dir(self, profile_points, direction, length,
                          x=0, y=0, z=0,
                          ifc_class="IfcBuildingElementProxy",
                          name="Extruded", material=None, storey=None):
        """
        Extrude profile along any direction vector.

        direction — (dx, dy, dz) tuple, will be normalised

        Example:
            # Inclined member at 30deg to horizontal
            import math
            tools.extrude_along_dir(profile,
                direction=(math.cos(math.radians(30)), 0, math.sin(math.radians(30))),
                length=5.0, ifc_class="IfcBeam")
        """
        d  = np.array(direction, dtype=float)
        d  = d / np.linalg.norm(d)
        # Find a reference direction perpendicular to d
        up = np.array([0, 0, 1]) if abs(d[2]) < 0.9 else np.array([1, 0, 0])
        ref = np.cross(d, up)
        ref = ref / np.linalg.norm(ref)

        ifc_dir = self._dir(float(d[0]), float(d[1]), float(d[2]))
        ifc_ref = self._dir(float(ref[0]), float(ref[1]), float(ref[2]))
        prof    = self._poly_profile(profile_points)
        ax3     = self.model.create_entity("IfcAxis2Placement3D",
                      Location=self._pt3(x,y,z),
                      Axis=ifc_dir, RefDirection=ifc_ref)
        extr    = self.model.create_entity("IfcExtrudedAreaSolid",
                      SweptArea=prof, Position=ax3,
                      ExtrudedDirection=ifc_dir, Depth=float(length))
        shape   = self._make_rep([extr])
        e = self._add_to_model(ifc_class, name, shape, storey, material)
        self._place_matrix(e, self._matrix(x, y, z))
        return e

    # ── Boolean operations ────────────────────────────────────────────────

    def _get_solid(self, element):
        """Extract the first solid item from an element's representation."""
        try:
            rep = element.Representation.Representations[0]
            return rep.Items[0]
        except Exception:
            raise ValueError(f"Cannot extract solid from {element.is_a()} — "
                             "element must have a SweptSolid representation")

    def subtract(self, base_element, tool_element,
                 name=None, ifc_class=None, storey=None):
        """
        Boolean subtract: base_element MINUS tool_element.
        Result replaces base_element's geometry.

        Note: IFC boolean results render correctly in most viewers
        (BIMvision, Solibri, IfcOpenShell viewer). FreeCAD mesh
        preview may not show the cut — check via Export IFC.

        Example:
            wall = ctx.make_wall(5, 3, 0.2)
            hole = ctx.make_column(height=3, diameter=0.5, x=2, y=0)
            tools.subtract(wall, hole, name="WALL-WITH-HOLE")
        """
        base_solid = self._get_solid(base_element)
        tool_solid = self._get_solid(tool_element)

        boolean = self.model.create_entity("IfcBooleanResult",
            Operator="DIFFERENCE",
            FirstOperand=base_solid,
            SecondOperand=tool_solid)

        rep = self.model.create_entity("IfcShapeRepresentation",
            ContextOfItems=self.ctx.body,
            RepresentationIdentifier="Body",
            RepresentationType="CSG",
            Items=[boolean])
        shape = self.model.create_entity("IfcProductDefinitionShape",
            Representations=[rep])

        # Update base element representation
        base_element.Representation = shape
        if name:
            base_element.Name = name
        return base_element

    def union(self, element_a, element_b,
              name=None, ifc_class=None, storey=None):
        """
        Boolean union: element_a UNION element_b.
        Returns element_a with combined geometry.

        Example:
            col  = ctx.make_column(height=3, diameter=0.4, x=0, y=0)
            base = ctx.make_footing(1.2, 1.2, 0.4, x=-0.4, y=-0.4)
            tools.union(col, base, name="COL-WITH-BASE")
        """
        solid_a = self._get_solid(element_a)
        solid_b = self._get_solid(element_b)

        boolean = self.model.create_entity("IfcBooleanResult",
            Operator="UNION",
            FirstOperand=solid_a,
            SecondOperand=solid_b)

        rep = self.model.create_entity("IfcShapeRepresentation",
            ContextOfItems=self.ctx.body,
            RepresentationIdentifier="Body",
            RepresentationType="CSG",
            Items=[boolean])
        shape = self.model.create_entity("IfcProductDefinitionShape",
            Representations=[rep])

        element_a.Representation = shape
        if name:
            element_a.Name = name
        return element_a

    def intersect(self, element_a, element_b,
                  name=None, storey=None):
        """
        Boolean intersection: keep only the volume common to both elements.
        Returns element_a with intersection geometry.

        Example:
            cyl  = ctx.make_column(height=2, diameter=1.0)
            box  = ctx.make_slab(0.8, 0.8, 2.0, z=0)
            tools.intersect(cyl, box, name="INTERSECTION")
        """
        solid_a = self._get_solid(element_a)
        solid_b = self._get_solid(element_b)

        boolean = self.model.create_entity("IfcBooleanResult",
            Operator="INTERSECTION",
            FirstOperand=solid_a,
            SecondOperand=solid_b)

        rep = self.model.create_entity("IfcShapeRepresentation",
            ContextOfItems=self.ctx.body,
            RepresentationIdentifier="Body",
            RepresentationType="CSG",
            Items=[boolean])
        shape = self.model.create_entity("IfcProductDefinitionShape",
            Representations=[rep])

        element_a.Representation = shape
        if name:
            element_a.Name = name
        return element_a

    def copy(self, source_element, dx=0, dy=0, dz=0,
             name=None, storey=None):
        """
        Copy an IFC element to a new position.
        Creates a new entity with the same representation.

        Example:
            wall2 = tools.copy(wall1, dx=6)
        """
        ifc_class = source_element.is_a()
        new_name  = name or (str(getattr(source_element, "Name", "")) + "_copy")
        e = ifcopenshell.api.root.create_entity(self.model,
            ifc_class=ifc_class, name=new_name)
        # Share representation (geometry reference)
        e.Representation = source_element.Representation

        target_storey = storey or self.ctx.storey
        ifcopenshell.api.spatial.assign_container(self.model,
            relating_structure=target_storey, products=[e])

        # Get source position and offset
        try:
            loc = source_element.ObjectPlacement.RelativePlacement.Location.Coordinates
            sx = float(loc[0]) + dx
            sy = float(loc[1]) + dy
            sz = (float(loc[2]) if len(loc) > 2 else 0.0) + dz
        except Exception:
            sx, sy, sz = dx, dy, dz

        self._place_matrix(e, self._matrix(sx, sy, sz))
        return e

    def array(self, template_func, nx=1, ny=1, nz=1,
              dx=0, dy=0, dz=0):
        """
        Rectangular grid array — calls template_func(x, y, z) for each cell.

        Example — 4x3 column grid:
            cols = tools.array(
                lambda x,y,z: ctx.make_column(4, diameter=0.4, x=x, y=y),
                nx=4, ny=3, dx=6, dy=7)
        """
        elements = []
        for iz in range(nz):
            for iy in range(ny):
                for ix in range(nx):
                    e = template_func(ix*dx, iy*dy, iz*dz)
                    elements.append(e)
        return elements

    def polar_array(self, template_func, count, radius,
                    cx=0, cy=0, start_angle=0):
        """
        Circular array — equally spaced around a centre point.

        Example — 8 columns in a circle:
            cols = tools.polar_array(
                lambda x,y,z: ctx.make_column(4, diameter=0.3, x=x, y=y),
                count=8, radius=5.0)
        """
        elements = []
        for i in range(count):
            angle = start_angle + 2 * math.pi * i / count
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            e = template_func(x, y, 0)
            elements.append(e)
        return elements

    def mirror_x(self, source_element, axis_y=0, name=None):
        """Mirror element about Y axis (reflect X coordinate)."""
        try:
            loc = source_element.ObjectPlacement.RelativePlacement.Location.Coordinates
            sx, sy = float(loc[0]), float(loc[1])
            sz = float(loc[2]) if len(loc) > 2 else 0.0
        except Exception:
            sx, sy, sz = 0.0, 0.0, 0.0

        e = self.copy(source_element, name=name or
                      (getattr(source_element, "Name", "") + "_mirX"))
        mx = 2 * axis_y - sx
        self._place_matrix(e, self._matrix(mx, sy, sz))
        return e

    def mirror_y(self, source_element, axis_x=0, name=None):
        """Mirror element about X axis (reflect Y coordinate)."""
        try:
            loc = source_element.ObjectPlacement.RelativePlacement.Location.Coordinates
            sx, sy = float(loc[0]), float(loc[1])
            sz = float(loc[2]) if len(loc) > 2 else 0.0
        except Exception:
            sx, sy, sz = 0.0, 0.0, 0.0

        e = self.copy(source_element, name=name or
                      (getattr(source_element, "Name", "") + "_mirY"))
        my = 2 * axis_x - sy
        self._place_matrix(e, self._matrix(sx, my, sz))
        return e

    # ── Rotate shorthand (degrees) ────────────────────────────────────────

    def rotate(self, element, angle_z=0, angle_x=0, angle_y=0,
               cx=0, cy=0, cz=0):
        """
        Rotate element around one or more axes (degrees as keyword, radians via math).
        Applies Z then X then Y order.

        Examples:
            tools.rotate(wall, angle_z=math.pi/2)         # 90deg around Z
            tools.rotate(slab, angle_x=math.radians(15))  # 15deg slope
            tools.rotate(beam, angle_y=math.pi/4)         # 45deg around Y
            tools.rotate(elem, angle_z=math.pi/2,
                               angle_x=math.radians(10))  # combined
        """
        if angle_z:
            self.rotate_z(element, angle_z, cx=cx, cy=cy)
        if angle_x:
            self.rotate_x(element, angle_x, cy=cy, cz=cz)
        if angle_y:
            self.rotate_y(element, angle_y, cx=cx, cz=cz)
        return element

    # ── Boolean operations ────────────────────────────────────────────────
    #
    # NOTE: IFC boolean results (IfcBooleanResult) are part of the IFC schema
    # and work correctly in exported .ifc files opened in BIMvision, Revit etc.
    # However FreeCAD's mesh preview may not render them — use Export IFC
    # and open in an online viewer to see the result correctly.
    #
    # These create NEW elements with boolean geometry.
    # The original elements are NOT deleted — remove them manually if needed.

    def _get_solid(self, element):
        """Extract the first solid item from an element's Body representation."""
        try:
            for rep in element.Representation.Representations:
                if rep.RepresentationIdentifier == "Body":
                    return rep.Items[0]
        except Exception:
            pass
        raise ValueError(
            f"Cannot extract solid from {element.is_a()} '{element.Name}'. "
            "Element must have a Body SweptSolid representation.")

    def subtract(self, base_element, tool_element,
                 name=None, ifc_class=None, storey=None, material=None):
        """
        Subtract tool_element geometry FROM base_element (A - B).
        Creates a new element with the boolean result.

        NOTE: Works best in IFC viewers. FreeCAD mesh preview may show
        original shapes — use Export IFC to verify result.

        Example:
            # Cylinder column with hole cut through it
            col  = ctx.make_column(height=3, diameter=0.5, x=0, y=0)
            hole = ctx.make_column(height=3, diameter=0.2, x=0, y=0)
            col_with_hole = tools.subtract(col, hole, name="COL-HOLLOW")
        """
        try:
            solid_a = self._get_solid(base_element)
            solid_b = self._get_solid(tool_element)

            boolean = self.model.create_entity("IfcBooleanResult",
                Operator="DIFFERENCE",
                FirstOperand=solid_a,
                SecondOperand=solid_b)

            rep = self.model.create_entity("IfcShapeRepresentation",
                ContextOfItems=self.ctx.body,
                RepresentationIdentifier="Body",
                RepresentationType="CSG",
                Items=[boolean])
            shape = self.model.create_entity("IfcProductDefinitionShape",
                Representations=[rep])

            cls  = ifc_class or base_element.is_a()
            tag  = name or f"{getattr(base_element,'Name','')}_{getattr(tool_element,'Name','')}_SUB"
            e = ifcopenshell.api.root.create_entity(self.model,
                ifc_class=cls, name=tag)
            e.Representation = shape
            target = storey or self.ctx.storey
            ifcopenshell.api.spatial.assign_container(self.model,
                relating_structure=target, products=[e])
            self._place_matrix(e, np.eye(4))
            if material:
                ifcopenshell.api.material.assign_material(self.model,
                    products=[e], material=material)
            FreeCAD.Console.PrintMessage(
                f"[IFC] subtract: '{tag}' created. "
                "Export IFC to see boolean result in viewer.\n")
            return e

        except Exception as ex:
            raise RuntimeError(f"subtract() failed: {ex}") from ex

    def union(self, element_a, element_b,
              name=None, ifc_class=None, storey=None, material=None):
        """
        Unite element_a and element_b geometry (A + B).
        Creates a new element with the combined solid.

        Example:
            wall  = ctx.make_wall(5, 3, 0.2, x=0, y=0)
            pier  = ctx.make_column(height=3, diameter=0.4, x=2.5, y=0)
            combined = tools.union(wall, pier, name="WALL-WITH-PIER")
        """
        try:
            solid_a = self._get_solid(element_a)
            solid_b = self._get_solid(element_b)

            boolean = self.model.create_entity("IfcBooleanResult",
                Operator="UNION",
                FirstOperand=solid_a,
                SecondOperand=solid_b)

            rep = self.model.create_entity("IfcShapeRepresentation",
                ContextOfItems=self.ctx.body,
                RepresentationIdentifier="Body",
                RepresentationType="CSG",
                Items=[boolean])
            shape = self.model.create_entity("IfcProductDefinitionShape",
                Representations=[rep])

            cls = ifc_class or element_a.is_a()
            tag = name or f"{getattr(element_a,'Name','')}_{getattr(element_b,'Name','')}_UNI"
            e = ifcopenshell.api.root.create_entity(self.model,
                ifc_class=cls, name=tag)
            e.Representation = shape
            target = storey or self.ctx.storey
            ifcopenshell.api.spatial.assign_container(self.model,
                relating_structure=target, products=[e])
            self._place_matrix(e, np.eye(4))
            if material:
                ifcopenshell.api.material.assign_material(self.model,
                    products=[e], material=material)
            FreeCAD.Console.PrintMessage(
                f"[IFC] union: '{tag}' created. "
                "Export IFC to see boolean result in viewer.\n")
            return e

        except Exception as ex:
            raise RuntimeError(f"union() failed: {ex}") from ex

    def intersect(self, element_a, element_b,
                  name=None, ifc_class=None, storey=None, material=None):
        """
        Intersect element_a and element_b — keep only overlapping volume.

        Example:
            big_col = ctx.make_column(height=4, diameter=1.0, x=0, y=0)
            cutter  = ctx.make_slab(2, 2, 0.5, x=-1, y=-1, z=1.5)
            slice   = tools.intersect(big_col, cutter, name="COL-SLICE")
        """
        try:
            solid_a = self._get_solid(element_a)
            solid_b = self._get_solid(element_b)

            boolean = self.model.create_entity("IfcBooleanResult",
                Operator="INTERSECTION",
                FirstOperand=solid_a,
                SecondOperand=solid_b)

            rep = self.model.create_entity("IfcShapeRepresentation",
                ContextOfItems=self.ctx.body,
                RepresentationIdentifier="Body",
                RepresentationType="CSG",
                Items=[boolean])
            shape = self.model.create_entity("IfcProductDefinitionShape",
                Representations=[rep])

            cls = ifc_class or element_a.is_a()
            tag = name or f"{getattr(element_a,'Name','')}_{getattr(element_b,'Name','')}_INT"
            e = ifcopenshell.api.root.create_entity(self.model,
                ifc_class=cls, name=tag)
            e.Representation = shape
            target = storey or self.ctx.storey
            ifcopenshell.api.spatial.assign_container(self.model,
                relating_structure=target, products=[e])
            self._place_matrix(e, np.eye(4))
            if material:
                ifcopenshell.api.material.assign_material(self.model,
                    products=[e], material=material)
            FreeCAD.Console.PrintMessage(
                f"[IFC] intersect: '{tag}' created. "
                "Export IFC to see boolean result in viewer.\n")
            return e

        except Exception as ex:
            raise RuntimeError(f"intersect() failed: {ex}") from ex