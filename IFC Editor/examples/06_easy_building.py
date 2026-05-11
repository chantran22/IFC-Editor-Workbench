"""
Example 06 - Easy Building (Beginner API)
==========================================
Uses IFCContext helper — no IFC schema knowledge needed.
Same as Example 03 but written in 10 lines instead of 80.
Press F5 to run.
"""

# ctx and model are pre-available — no imports needed for basic use

ctx.setup("Easy Building")
conc = ctx.material("Concrete C30", "concrete")
masn = ctx.material("Masonry",      "masonry")



# Perimeter walls
import math
s1= ctx.make_wall(9.4, 3.5, 0.2,  x=0,    y=0,    angle_z=0,     name="WALL-S", material=masn)
tools.translate(s1, dx=0, dy=7.4, dz=0.2)
s2= tools.copy(s1, dx=0, dy= -14.8, dz=0)

s3= ctx.make_wall(15, 3.5, 0.2,  x=0,    y=0,  angle_z= 0,       name="WALL-N", material=masn)
tools.rotate(s3, angle_z= math.pi/2)
s3= tools.translate(s3, dx=4.8, dy=0, dz=0.2)

s4= ctx.make_wall(15, 3.5, 0.2,  x=0,    y=0,  angle_z= 0,       name="WALL-N", material=masn)
tools.rotate(s4, angle_z= -math.pi/2)
s4= tools.translate(s4, dx=-4.8, dy=0, dz=0.2)

# # Ground slab
ctx.make_slab(10.4, 15.4, 0.2, x=0, y=0, z=0, name="SLAB-GF", material=conc)
