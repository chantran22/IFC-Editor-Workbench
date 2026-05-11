"""
Example 07 - Easy Column Grid (Beginner API)
=============================================
Array of columns using ctx.array() — 3 lines of code.
Press F5 to run.
"""

ctx.setup("Column Grid")
conc = ctx.material("RC Concrete", "concrete")

# Array: 4 columns x 3 rows, 6m x 7m spacing
ctx.array(
    lambda x, y, z: ctx.make_column(
        height=4.0, diameter=0.4,
        x=x, y=y,
        name=f"COL-{int(x/6)+1}-{int(y/7)+1}",
        material=conc),
    nx=4, ny=3, dx=6, dy=7)

print(f"Done: {ctx.element_count()} columns")
