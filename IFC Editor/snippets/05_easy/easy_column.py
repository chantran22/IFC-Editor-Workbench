"""Easy column — circular or rectangular."""
# Circular column
col = ctx.make_column(height=3.5, diameter=0.4,
    x=0, y=0, name="COL-01", material=conc)

# Rectangular column (uncomment to use instead)
# col = ctx.make_column(height=3.5, width=0.4, depth=0.5,
#     x=0, y=0, name="COL-01", material=conc)
