# Site pack: flat patterns for the website

What the website's shape pages are made from (item 7288), written by
`python scripts/site_pack.py`: for every shape family, two common sizes,
each with its flat as SVG, its cut file as DXF and as DXF R12, and its 3D
model as one web page. pack.json lists every entry and file and is held to
pack.schema.json. Sizes are in mm, with inches beside them.

| Shape | Sizes | Pieces |
| --- | --- | --- |
| Rolled cylinder | 1000 mm diameter, 800 mm high, 6 mm plate; 630 mm duct diameter, 1000 mm long, 1 mm sheet | 1, 1 |
| Cone and frustum | 1000 mm to 500 mm, 800 mm high, 6 mm plate; 500 mm to 315 mm duct, 300 mm long, 0.8 mm sheet | 1, 1 |
| Oblique and eccentric cone | 1000 mm to 500 mm, offset 200 mm, 6 mm plate; 400 mm to 250 mm duct, offset 75 mm, 300 mm long, 0.8 mm sheet | 1, 1 |
| Multi-course shell | 2000 mm shell narrowing to 1200 mm, 6 mm plate; 1200 mm shell narrowing to 800 mm, 3 mm plate | 4, 3 |
| Square-to-round | 600 x 400 mm to 300 mm round, 500 mm high, 3 mm plate; 500 x 300 mm duct to 250 mm round, 300 mm long, 0.8 mm sheet | 1, 1 |
| Round-to-round transition | 800 mm to 500 mm, offset 150 mm, top tilted 30 degrees, 5 mm plate; 400 mm to 250 mm duct on one centre line, 300 mm long, 0.8 mm sheet | 1, 1 |
| Rectangle-to-rectangle and hopper | 600 x 400 mm to 300 x 200 mm, 500 mm high, 3 mm plate; 1000 x 500 mm to 600 x 400 mm, 600 mm high, 3 mm plate | 1, 1 |
| Transition between any two sections | rectangle 600 x 400 mm to round 300 mm; rectangle 800 x 400 mm to round 400 mm, 600 mm high | 1, 1 |
| Segmented (lobster-back) elbow | 300 mm diameter, 90 degrees in 4 pieces, 3 mm plate; 12 inch pipe (323.9 mm outside), 90 degrees in 5 pieces, 6 mm plate | 4, 5 |
| Reducing segmented elbow | 400 mm to 250 mm, 90 degrees in 4 pieces, 3 mm plate; 300 mm to 200 mm, 60 degrees in 3 pieces, 5 mm plate | 4, 3 |
| Tee | 400 mm main with a 200 mm branch, 6 mm plate; 8 inch main (219.1 mm) with a 4 inch branch (114.3 mm), 6 mm plate | 2, 2 |
| Lateral | 400 mm main with a 200 mm branch at 45 degrees, 6 mm plate; 12 inch main (323.9 mm) with a 6 inch branch (168.3 mm) at 45 degrees, 6 mm plate | 2, 2 |
| Y-piece (breeches) | 300 mm main with two 300 mm legs at 30 degrees, 5 mm plate; 200 mm main with two 200 mm legs at 30 degrees, 3 mm plate | 3, 3 |
| Pipe on a cone | 600 mm to 300 mm cone with a 150 mm branch, 4 mm plate; 800 mm to 400 mm cone, 600 mm high, with a 6 inch branch (168.3 mm), 4 mm plate | 2, 2 |
| Cone on a pipe | 400 mm main with a 250 mm to 150 mm cone branch, 6 mm plate; 600 mm main with a 400 mm to 250 mm cone branch, 8 mm plate | 2, 2 |
| Cone on a cone | 600 mm to 300 mm cone with a 200 mm to 120 mm branch, 4 mm plate; 800 mm to 400 mm cone, 600 mm high, with a 250 mm to 150 mm branch, 4 mm plate | 2, 2 |
| Pipe through a plate | 150 mm pipe through a level 4 mm plate; 300 mm pipe through a plate sloped 60 degrees, 10 mm plate | 2, 2 |
| Header: branches on a body | 400 mm x 1500 mm pipe with two 200 mm branches, 6 mm plate; 24 inch body (610 mm) x 2000 mm with two 12 inch branches (323.9 mm), 6 mm plate | 3, 3 |
| Branch on an elbow piece | 100 mm branch on piece 2 of a 300 mm elbow, 3 mm plate; 150 mm branch on piece 2 of a 500 mm elbow, 5 mm plate | 2, 2 |
| Branch on a transition face | 80 mm branch on the front face of a 600 x 400 to 300 transition, 3 mm plate; 200 mm branch on the front face of a 1000 x 1000 to 600 transition, 800 mm high, 3 mm plate | 2, 2 |
| Rectangular radius elbow | 400 x 300 mm, 150 mm throat radius, 90 degrees, 1 mm sheet; 600 x 400 mm duct, 150 mm throat radius, 90 degrees, 1 mm sheet | 4, 4 |
| Rectangular offset | 400 x 300 mm, 200 mm over 600 mm, 1 mm sheet; 600 x 400 mm duct, 300 mm over 900 mm, 1 mm sheet | 4, 4 |
| Rectangular Y-branch | 600 x 300 mm into two 300 mm legs at 45 degrees, 1 mm sheet; 800 x 400 mm into two 400 mm legs at 45 degrees, 1 mm sheet | 6, 6 |
| Rectangular duct reducer | 600 x 400 mm to 400 x 300 mm over 500 mm, 1 mm sheet; 800 x 400 mm to 600 x 400 mm over 500 mm, 1 mm sheet | 4, 4 |
| Rectangular duct shoe tap | 300 x 200 mm, 150 mm high, 100 mm shoe, 1 mm sheet; 400 x 300 mm, 200 mm high, 100 mm shoe, 0.8 mm sheet | 5, 5 |
