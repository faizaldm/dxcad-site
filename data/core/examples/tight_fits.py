# SPDX-License-Identifier: Apache-2.0
"""A shaft in a housing with two collars and a cover, at fits of 0.05 to 0.2 mm.

The shaft runs in the housing's bore with FIT all round, each collar holds the
shaft with COLLAR_FIT all round, the lower collar stands GAP under the housing
and the cover GAP off its side. The upper collar is meant to stand just clear
of the housing's top, but STOP is -0.05: it runs 0.05 mm into it. Model >
Check Interference... finds that overlap, and "Also list pairs closer than
0.25 mm" lists the tight gaps with the overlap; set STOP = 0.1 to mend it.

Tags: assembly
"""

FIT = 0.1  # the bore's clearance round the shaft, mm
COLLAR_FIT = 0.05  # each collar's clearance round the shaft, mm
GAP = 0.2  # the lower collar under the housing, and the cover off its side, mm
STOP = -0.05  # the upper collar over the housing's top, mm: below 0 runs into it

SHAFT = 10.0  # the shaft's radius
LENGTH = 80.0  # the shaft's length
BLOCK = 40.0  # the housing, a cube
BOTTOM = 20.0  # the housing's underside, above the shaft's lower end
COLLAR = 16.0  # a collar's outer radius
COLLAR_LENGTH = 8.0
AXIS = (BLOCK / 2, BLOCK / 2)

bore = make_cylinder(SHAFT + FIT, BLOCK + 2, (*AXIS, BOTTOM - 1))
part("housing", cut(make_box(BLOCK, BLOCK, BLOCK, (0, 0, BOTTOM)), bore), color="steel")
part("shaft", make_cylinder(SHAFT, LENGTH, (*AXIS, 0)), color="hardware")

low = BOTTOM - GAP - COLLAR_LENGTH
high = BOTTOM + BLOCK + STOP
for name, z in (("collar_low", low), ("collar_high", high)):
    ring = make_cylinder(COLLAR, COLLAR_LENGTH, (*AXIS, z))
    hole = make_cylinder(SHAFT + COLLAR_FIT, COLLAR_LENGTH + 2, (*AXIS, z - 1))
    part(name, cut(ring, hole), color="brass")

part("cover", make_box(5, BLOCK, BLOCK, (BLOCK + GAP, 0, BOTTOM)), color="navy")
