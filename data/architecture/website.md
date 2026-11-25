# DX-CAD Architecture

Model small buildings in DX-CAD: layered walls, floors, roofs, doors, windows, stairs, columns and beams, each built from tables you can edit. Every element is a real solid you can measure, and plans, elevations, schedules and quantities come straight from the model.

## Walls the way they are built

Each wall is built from a wall type: its layers, from the outside face to the inside face, listed in a table you can edit. Walls run straight or along an arc. Where two walls meet, you choose how each end is finished, butt or mitre, and nothing is joined or trimmed unless you ask.

## Floors, ceilings and roofs

Floors and ceilings are built from a boundary you type and a slab type. Roofs are built over a footprint with a slope on each edge, so one command makes a hipped roof, a gabled roof or a mix, with a thickness and an overhang. Cut a hole you draw through a floor, ceiling or roof for a stair or a rooflight.

## Doors and windows

Put a door or a window in a wall and the wall is cut by its opening, through every layer. Doors and windows come from type tables (single, double and sliding doors; windows divided by mullions and transoms) or from the sizes you give. They go in straight walls and in curved ones, where the frame sits in an opening with parallel jambs so it fits.

## Stairs and railings

Straight, L, U, winder and spiral stairs are laid out from a stair rules table that holds the riser and going limits you work to. Stair railings follow each flight at the handrail height the table gives, with posts no further apart than it allows. Level railings and glass balustrades follow the points you give.

## Columns and beams

Columns and beams take their sizes from a sections table: I and H sections, hollow sections, channels, angles, tees and solid rectangles. Place columns one by one or on an array of rows and columns.

## Rooms and quantities

Draw a room's boundary and give it a name, a number and a height; its area, perimeter and volume follow from what you drew. Quantities lists lengths, net areas, volumes and counts for walls, slabs, roofs, members, doors, windows and rooms, measured from the solids as built, and saves them as a CSV file.

## Drawings

Put plan views cut at a height you choose, elevations of each side, and door, window and room schedules on a drawing sheet. Schedules are read only: they always show the model as it is.

## IFC export

Export the model to an IFC4 file for others to open. Walls, floors, ceilings, roofs, doors, windows, stairs, railings, columns and beams go on their levels' storeys, each with its type, its layers and their materials, and the site's survey coordinates and true north. Straight sweeps keep their exact shape, arcs included.

## Levels, types and site

Storeys are DX-CAD's levels: change a level's height and everything on it moves with it. Walls, floors, doors, windows, stairs, columns and beams name their types. The project's base point, survey coordinates and true north are kept with the file.

## Metric and imperial

Lengths are typed in millimetres or in feet and inches. Starter projects come in both: a small two-storey building, and a single-storey house with a garage. Three more, in millimetres, start a small house, a detached garage or an office extension. A four-bedroom villa shows the whole add-on, stage by stage.

## Checked, every time

Accuracy is the product. The add-on's tests check every kind of shape it makes against lengths, areas and volumes worked out by hand, and check every solid it makes for validity.

## Trial and licence

Architecture is free during DX-CAD's 30-day trial while no licence key is held; after that it needs an Architecture licence. It is an add-on for DX-CAD 0.1.7 and later.
