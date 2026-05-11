"""Easy wall — ctx.make_wall(length, height, thickness, x, y, angle_z)"""
import math
wall = ctx.make_wall(
    length=5.0, height=3.0, thickness=0.2,
    x=0, y=0, z=0,
    angle_z=0,        # rotation: 0=along X, math.pi/2=along Y
    name="WALL-01",
    material=masn)    # replace masn with your material variable
