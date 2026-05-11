"""Easy array — repeat any element in a grid."""
# Example: 4x3 grid of columns, 6m x 7m spacing
ctx.array(
    lambda x, y, z: ctx.make_column(
        height=4.0, diameter=0.4,
        x=x, y=y, name=f"COL-{int(x/6)+1}-{int(y/7)+1}",
        material=conc),
    nx=4, ny=3,    # columns x rows
    dx=6, dy=7)    # spacing X and Y
