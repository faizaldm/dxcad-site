# DX-CAD Architecture: its commands and starters

Copied from DX-CAD Architecture 0.1.0's docs/guide/index.md (the owner's approval, 25 November 2026).

## Commands

- Wall...: Makes a layered wall, straight or along an arc, as one part holding a solid per layer.
- Join Walls...: Joins one end of a wall to another wall with the treatment you choose: butt or mitre.
- Door...: Puts a door in the picked wall and cuts the wall by the door's opening.
- Window...: Puts a window in the picked wall at a sill height and cuts the wall by its opening.
- Opening in Wall...: Cuts a plain rectangular opening, with nothing in it, through the picked wall.
- Floor...: Makes a floor slab from a closed boundary you type and a slab type.
- Ceiling...: Makes a ceiling from a closed boundary and a slab type, built as a floor is.
- Roof...: Makes a roof over a convex footprint with a slope on each edge: hipped, gabled or a mix.
- Hole in Floor or Roof...: Cuts a hole you draw plumb through the picked floor, ceiling or roof, such as a stair void.
- Stair...: Makes a straight, L, U or winder stair between two heights from the stair rules table.
- Spiral Stair...: Makes a spiral stair about a centre, its risers from the stair rules table.
- Railing...: Makes a level railing along the points you type, on square posts.
- Balustrade...: Makes a glass balustrade along the points you type: glass panels under a handrail from the sections table.
- Stair Railing...: Makes a railing that follows the picked stair's flights, its height and post spacing from the stair rules table.
- Columns...: Makes a column of a section at each point you type, from a base to a top height.
- Column Array...: Makes columns of a section on an array you type: rows, columns and the two spacings, from a first column and a direction.
- Beam...: Makes a member of a section between two points, turned about its line.
- Room...: Makes a room from the boundary you type, with a name, a number and a height; Quantities lists its area, perimeter and volume.
- Plant...: Makes a tree, palm, cypress, hedge, clipped ball, shrub, lavender or grass clump of a species from the plants table, shaped by a seed that repeats.
- Plants Along Line...: Plants a row along the line you type, a spacing apart, kept clear of walls, floors and paths.
- Plants in Area...: Scatters plants over the area you draw, as many as the density asks, a minimum gap apart, kept clear of walls, floors and paths.
- Hedge...: Makes a clipped hedge along the line you type, at the height and width you give.
- Ground Area...: Makes a planting bed, a lawn, gravel, paving or asphalt over the boundary you draw, from the ground types table.
- Room Lights...: Puts a ceiling fitting and its lamp in each room you drew, at its centre or on a grid, at the room's ceiling.
- Light...: Puts a light fitting and its lamp at a point you type.
- Lights Along Line...: Puts a light fitting and its lamp every spacing along the line you type.
- Wall Light...: Puts a wall light or lantern and its lamp on the face of the wall you picked, at a height.
- Plant Uplight...: Puts an uplight and its lamp on the ground near the foot of a plant, shining up.
- Pool Light...: Puts a pool light and its lamp on the pool's wall, under the water line, shining into the pool.
- Quantities...: Shows read-only tables of lengths, areas, volumes and counts, and saves them as CSV if asked.
- Materials...: Lists the material each wall, floor, ceiling, roof, door, window and ground type in the model names, layer by layer, from the tables, read only.
- Export IFC...: Writes the model's walls, floors, roofs, doors, windows, stairs, railings, columns and beams to an IFC4 file, on their levels' storeys, with their types and layers.
- Plan View...: Puts a plan of the model on the drawing in front: what a level cut passes through drawn thick, what lies below it drawn thin, hidden lines removed.
- Elevation View...: Puts an elevation of the building on the drawing in front: the building seen square to one side, north, east, south or west, hidden lines removed, over a ground line.
- Schedule View...: Puts a read-only schedule on the drawing in front: the doors and windows by type with their marks, or the rooms by number.
- Site Coordinates...: Keeps the project base point, its survey coordinates and the true north angle with the file.
- Named Camera...: Keeps a camera with the file, by name, so pictures before and after a change are taken from the same place.
- Named Cameras from Table...: Keeps every camera of a named cameras table with the file, so a set of views is ready for Open Named Camera... and Render Preset....
- Open Named Camera...: Turns DX-CAD's 3D view to a camera kept with Named Camera..., so the model is seen from where a picture is taken.
- Render Preset...: Works out what a render preset sets for a named camera: the camera, the sky, the sun from the site's location, the exposure and the lights, keeps it with the file, and, given a picture file, draws the picture with DX-CAD's photo-real render.
- Estate Views...: Adds a table's views to the open project as DX-CAD's own named cameras, says what stands in their way and, given a folder, draws each one with the render presets of its place.
- Camera Set...: Adds named cameras round the building and one in each room you have drawn, or those of a table, and keeps the render set that pairs each camera with the render presets of its place.

## Starters

- examples/starter_small_house.py: a two-storey house with a stair, a hip roof and a room on each storey.
- examples/starter_garage.py: a detached single garage with a gable roof.
- examples/starter_office_extension.py: an office and a WC against an existing building's wall, under a mono-pitch roof.
- examples/starter_bungalow_metric.py and examples/starter_bungalow_imperial.py: a single-storey house with an attached garage.
- examples/starter_metric.py and examples/starter_imperial.py: a two-storey building on two levels.
