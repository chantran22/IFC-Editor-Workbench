"""
Example 08 - IFC Tools Demo
=============================
Demonstrates: extrude, sweep, array, polar_array, copy, mirror, loft.
Uses tools.* commands — similar to Part WB / CadQuery style.
Press F5 to run.
"""
import math

ctx.setup("IFC Tools Demo")
conc  = ctx.material("Concrete", "concrete")
steel = ctx.material("Steel",    "steel")
wood  = ctx.material("Timber",   "wood")

# ── 1. Extrude — L-section steel beam ─────────────────────────────────
profile_L = tools.make_profile_L(width=0.1, height=0.15, thickness=0.01)
beam = tools.extrude(profile_L, depth=6.0,
    x=0, y=0, z=3.0,
    ifc_class="IfcBeam", name="L-BEAM-01", material=steel)

# ── 2. Extrude — I-section column ─────────────────────────────────────
profile_I = tools.make_profile_I(width=0.2, height=0.3,
                                  web_thickness=0.01, flange_thickness=0.015)
col_I = tools.extrude(profile_I, depth=3.0,
    x=0, y=0, z=0,
    ifc_class="IfcColumn", name="I-COL-01", material=steel)

# ── 3. Array — 4x3 rectangular grid of I-columns ──────────────────────
tools.array(
    lambda x, y, z: tools.extrude(
        tools.make_profile_I(0.2, 0.3, 0.01, 0.015),
        depth=3.0, x=x+6, y=y, z=0,
        ifc_class="IfcColumn",
        name=f"I-COL-{int(x/6)+2}-{int(y/7)+1}",
        material=steel),
    nx=3, ny=3, dx=6, dy=7)

# ── 4. Polar array — 6 columns in a circle ────────────────────────────
tools.polar_array(
    lambda x, y, z: ctx.make_column(
        height=4.0, diameter=0.35,
        x=x+30, y=y+15,
        name="CIR-COL",
        material=conc),
    count=6, radius=4.0,
    cx=0, cy=0)

# ── 5. Sweep — circular pipe along L-path ─────────────────────────────
pipe_profile = tools.make_profile_circle(radius=0.05, segments=12)
pipe = tools.sweep(pipe_profile,
    path_points=[(20, 0, 0), (20, 0, 2), (20, 5, 2), (25, 5, 2)],
    ifc_class="IfcPipeSegment", name="PIPE-01", material=steel)

# ── 6. Copy + translate ────────────────────────────────────────────────
beam2 = tools.copy(beam, dy=7, name="L-BEAM-02")
beam3 = tools.copy(beam, dy=14, name="L-BEAM-03")

# ── 7. Mirror ─────────────────────────────────────────────────────────
col_mirror = tools.mirror_y(col_I, axis_x=10, name="I-COL-MIRROR")

# ── 8. Loft — tapered column (rect base → circle top) ─────────────────
loft_col = tools.loft(
    profiles_with_z=[
        (0.0, tools.make_profile_rect(0.6, 0.6)),
        (2.0, tools.make_profile_rect(0.4, 0.4)),
        (4.0, tools.make_profile_circle(0.2, 16)),
    ],
    ifc_class="IfcColumn",
    name="LOFT-COL", material=conc)

print(f"Done: {ctx.element_count()} elements")
print("Operations used: extrude, array, polar_array, sweep, copy, mirror, loft")