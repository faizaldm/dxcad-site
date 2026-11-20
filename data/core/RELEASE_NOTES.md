# Release notes

What each release of DX-CAD brings, in plain words, newest first. The full
record of every change is in [CHANGELOG.md](CHANGELOG.md).

## 0.1.7

An update to 0.1.6, 20 November 2026. It installs over 0.1.6, and your
files, settings and add-ons are kept. DX-CAD now makes photo-real pictures:
finishes, daylight, lamps and an architect's camera, with its own renderer
for a quick preview and Blender for finished pictures, a whole set of
cameras in one unattended run, and render packs that sweep cameras, light
and looks into drafts to pick from. Drawings of big assemblies show an outline
at once and let you pick how much detail each view shows. Parts can be
turned with Edit > Rotate.... Add-ons get plugin API 9, and assistants such
as Claude Desktop can use add-ons' commands and render in the background.

### Rendering

- View > Render... makes a photo-real still, Draft, Good or Final, with a
  bar and Cancel; the grain is smoothed away. It is the quick preview.
  <!-- 1183, 1184, 1193, 1206 -->
- Finishes such as oak, brick, glass, water, grass and lawn, each with its
  texture, given to a part or a face in the Render box's Materials... or in
  the model with `finish=`; their colour, roughness and tile can be changed.
  <!-- 1185, 1190, 1191, 1192, 1203, 1212 -->
- Daylight from a clear sky, with the sun where it is at your site at the
  time and date you give, or your own HDR picture; a daylight render sets
  its own exposure, and the project keeps its site and its parts' looks.
  <!-- 1186, 1221, 1222 -->
- Lamps in lumens and kelvin, points, spots, areas and glowing parts, kept
  in the project. <!-- 1187, 1194, 1195 -->
- An architect's camera, with eye height, a lens in mm, upright verticals
  and depth of field; named cameras are kept in the project and the picture
  is named after its camera. <!-- 1188, 1196, 1197, 1209 -->
- Parts render in their own colours, leaves from both sides, glass and water
  see-through, and grass and lawn look like turf. <!-- 1207, 1208, 1219 -->
- Finished pictures come from Blender: File > Export for Render... hands it
  the scene, the Render box can render in Blender, and DX-CAD finds Blender
  itself. <!-- 1189, 1205 -->
- File > Render Set in Blender... and `dxcad render-set` render every
  camera of a set in one unattended run, skip what is done already, carry
  on past a failed picture and make a contact sheet. <!-- 1227 -->
- File > Render Pack... and `dxcad render-pack` sweep one recipe of cameras,
  lenses, heights, times of day, dates, skies, HDR pictures, exposures,
  depth of field and lamps into quick drafts on a contact sheet, then render
  only the ones you tick at final quality. <!-- 1229 -->

### Modelling

- Edit > Rotate... turns the picked parts, or a sub-assembly as one, about
  an axis you pick or type, by an angle you type, in one undo step.
  <!-- 1162 -->
- Big models build faster: their booleans now use every core of the
  machine, and every shape comes out the same. <!-- 1180, 1215 -->
- Animate's build video is framed once and turns at a steady speed, and can
  carry captions from a CSV file. <!-- 1158 -->
- Colours given to parts made in a function or a loop are kept in the view,
  in renders and in saved assemblies. <!-- 1156 -->

### Drawings

- On a big assembly each view first shows the model's outline, then a bar
  on the view lets you pick the detail: the outline, the sub-assemblies,
  the parts, or the parts and their fasteners. Quick draft lines show while
  the exact ones are worked out; Cancel keeps what is drawn, and a saved
  drawing opens at its levels.
  <!-- 1163, 1166, 1167, 1168, 1169, 1170, 1173, 1174, 1214 -->
- PDF, DXF and Print always get the exact lines, at each view's level.
  <!-- 1171 -->
- Moving a view, or changing a note or a dimension, takes under a second on
  a big model, and a balloon finds its place at once.
  <!-- 1164, 1165, 1175, 1226 -->
- The time each level takes is measured on the three biggest models.
  <!-- 1172 -->
- `dxcad drawing --table FILE.csv` puts a table from a CSV file on the
  drawing's sheets. <!-- 1160 -->

### Add-ons and the plugin API

- Plugin API 8: an add-on can read each drawing view's level of detail and
  its lines, name its undo steps, show words and progress from its sheet
  tools, give its fields a tip and a unit, style the lines of its own views
  and tell which of its views was clicked. <!-- 1176, 1177, 1201 -->
- Add-ons for buildings can rewrite a part's line whatever it carries, list
  levels and types in their dialogs, host elements that move with their
  host and cut every layer of a wall, count and total their schedules, and
  offer starter projects. <!-- 1178, 1198, 1199, 1200, 1202, 1210, 1211, 1213 -->
- Plugin API 9: add-ons can give finishes, lamps and cameras and render,
  hand back shapes in their own colours, keep their data in the project
  with Undo, be called after each run and as a project opens, and add rows
  to a render set. Add-ons written for earlier APIs load as before.
  <!-- 1204, 1216, 1224, 1225 -->

### Agents and Claude Desktop

- An assistant such as Claude Desktop can capture the view at the size it
  asks with only the parts it names, use your add-ons' own commands, and
  start a long render, or a render pack's stage, that goes on after its
  reply, asking how it stands or stopping it. <!-- 1159, 1217, 1223 -->

### Licensing

- Architecture is on sale beside Drafting Pro and Fabrication, so the
  30-day trial unlocks all three. <!-- 1153 -->
- The add-ons show their price, GBP 129 for Drafting Pro, GBP 189 for
  Fabrication and GBP 169 for Architecture, and Buy opens the pricing on
  dxcad.designmatix.co.uk. <!-- 1182, 1228 -->
- Help > Licence and `dxcad licence status` say the day your licence ends,
  then the day it works offline until, and "1 seat" for one. <!-- 1181 -->

### Install

- The release is checked by installing it on a second Windows laptop, and
  the test suite and its macOS and Linux runs were put right after 0.1.6's.
  <!-- 1154, 1155, 1157, 1179 -->

### Fixes

- Big renders come out whole, never black or striped, and the shade under
  eaves is smooth. <!-- 1218, 1220 -->
- Export 3D PDF and Export 3D Web Page show one progress bar while they
  work, and no DX-CAD dialog pops up over another program. <!-- 1161 -->

### Known limitations

- Blender's pictures, and its day sky on Blender 5, have not been checked
  by eye for this release: the tests use a stand-in for Blender. DX-CAD's
  own renderer needs the graphics card's OpenGL, and on macOS it does not
  render from the command line or for an assistant.
- A drawing view saved at Outline or Sub-assemblies takes a few seconds the
  first time Balloon View asks for its regions on a big model.
- The window bench, which allows a big showcase model 10 seconds to open,
  can still be missed on a slow laptop by race_car_frame's rebuild and
  steel_structure's opening, though both are faster than in 0.1.6; the
  models open and work.
- Those of 0.1.6 and 0.1.0, below, still hold, but for hidden lines on a
  very big assembly, which now show an outline and draft lines first.

## 0.1.6

An update to 0.1.5, 13 November 2026. It installs over 0.1.5, and your
files, settings and add-ons are kept. Drawings get clearer dimensions you
can style, make your own and edit, and title-block values you change where
they stand. Long work shows how far it has got and can be cancelled.
STEP and DXF files come in through a wizard, mates are edited from the
Feature tree, and a model can hold levels, types, hosted elements and
schedules. Claude Desktop can be allowed to build models, and changes many
lines at once. Add-ons get plugin API 7.

### Modelling

- Connect Claude Desktop now asks once whether Claude may run models. In
  0.1.5 it could change a model's lines but never build it; Allow lets it
  run a trusted project's model, and Settings > Runs changes your answer.
- Claude Desktop changes several places in a model in one step, one undo
  for the lot, so a change to a big model takes far less time.
- File > Import... brings in a STEP file or a DXF drawing step by step,
  checking what it holds, and its units, before anything is added.
- Right-click or double-click a mate in the Feature tree to change its kind
  and value, or delete it, one undo step.
- A model can name levels and grid lines and stand parts on a level, give
  elements a type whose values they override one by one, host an element in
  another so it cuts it and moves with it, and list element values in a
  read-only schedule you can save as CSV. View > Project Browser lists the
  levels, drawings and schedules.

### Drawings

- Dimensions keep clear of the views and of their own text. Drawing
  properties > Dimensions sets the arrow size, text height, gaps and
  spacing; Settings > Drawings sets them for new drawings.
- Make Dimensions Editable turns a view's automatic sizes and hole callouts
  into dimensions of your own, to move, edit, type over and delete.
- Double-click a title-block value on the sheet to change it there.
- "Please wait" shows a bar, the percent done and the time left, and Cancel
  stops an export with nothing written.
- The sheet on screen draws what the PDF draws, its texts centred where
  they belong; a long status message can be read in full by clicking it.
- Hidden lines on big assemblies are worked out faster, every line as
  before.

### Measure

- Check Interference... can also list the pairs of parts closer than a gap
  you type, each with its gap and a red line between the nearest points.

### Add-ons

- Plugin API 7: an add-on's commands can show their progress and be
  cancelled, be greyed with their own reason and carry tooltips; its
  drawing views follow the drawing's units and turn by 90 degrees; its sheet
  tools can take clicks until Enter; and its flat patterns can carry
  marking on layers of their own and go several to one DXF. Add-ons for
  buildings can read a model's levels, types, hosts and schedules.

### Known limitations

- Hidden lines on a very big assembly still take minutes for each view;
  the quick outline shows meanwhile, with a notice on the sheet.
- Those of 0.1.0, below, still hold.

## 0.1.5

An update to 0.1.4, 3 November 2026. It installs over 0.1.4, and your
files, settings and add-ons are kept. It makes DX-CAD easier to drive, by
you and by an AI assistant such as Claude Desktop: the script editor finds
and goes to lines, agents can read and change a model by its lines and
frame the view, a project's model runs only once you have trusted it, and
saved projects keep their colours and sheet metal. Drawings gain editable,
movable title-block texts and dimensions in two units.

### Modelling

- The script editor: Edit > Go to Line (Ctrl+G), a Find bar (Ctrl+F, F3,
  Shift+F3) and Replace (Ctrl+H), Replace All being one undo step.
- Claude Desktop and other agents can read the script pane, find a line,
  change only the lines that need changing and run the model, so a small
  change to a long model no longer means writing the whole model again.
  They can also set and fit the live view, select and isolate parts, and
  take a picture of the view as you see it.
- File > Trust This Project's Model: a model that came in a project file
  runs only once you have trusted it, and DX-CAD remembers your answer
  until the model changes. An agent cannot run it before you do.
- Running a model never writes the project file; only Save does. A
  reopened assembly keeps each part's colour and part number.
- Orthographic and perspective views, Fit Selection (Shift+F), arrow keys
  to pan, zoom about the cursor, and a choice of what the camera does after
  a run. Zoom Window now fits the box you draw.
- Settings > Assistant takes your AI provider's key, tests it and lists
  the provider's current models. Settings > Runs sets a run's time limit.

### Sheet metal

- A cut-out of any shape, such as a window with rounded corners, keeps the
  part as sheet metal, with true arcs in its flat pattern and DXF.
- A reopened project's sheet metal parts keep their flat patterns without
  running the model.

### Drawings

- Every text in the title block can be edited and moved.
- Dimensions in mm, inch, or both (mm [inch] or inch [mm]).
- New drawings have no centre marks until you turn them on.

### Install

- Starting DX-CAD again brings the open window to the front.
- Restart Claude Desktop, on the start page, works with the Microsoft
  Store edition of Claude Desktop.

### Known limitations

- Those of 0.1.0, below, still hold.

## 0.1.4

An update to 0.1.3, 1 November 2026. It installs over 0.1.3, and your
files, settings and add-ons are kept. It mends one thing: Connect Claude
Desktop, on the start page, now links Claude Desktop to an installed
DX-CAD.

### Install

- Connect Claude Desktop writes the command Claude Desktop needs to start
  DX-CAD's server in an installed DX-CAD, on Windows and on a Mac. Before,
  Claude Desktop could not connect. If you clicked it in an earlier
  version, click it again in 0.1.4, then restart Claude Desktop.

### Known limitations

- Those of 0.1.0, below, still hold.

## 0.1.3

An update to 0.1.2, 31 October 2026. It installs over 0.1.2, and your
files, settings and add-ons are kept; add-ons made for 0.1.2 work with it.
What is new: you can turn a drawing view by 90 degrees, cut holes and slots
across a bend in sheet metal, and add-ons can have toolbars of their own;
the macOS app opens without the "could not verify" box, and a few things
you may have met are fixed.

### Sheet metal

- Holes, rounded slots and cutouts across a bend: give them on the flat
  pattern with `bend_cut`, and they are cut as the shop floor cuts them,
  straight through each wall and wrapped round the bend. A cut may cross
  several bends in a row. Cut in the window, through one face and on across
  a bend, now keeps the part as sheet metal instead of being refused.
- The flat pattern breaks a bend line only where a cut across the bend
  crosses it; other holes and openings leave it whole, as in 0.1.2.

### Drawings

- Turn a drawing view by 90, 180 or 270 degrees: set Rotation in Drawing
  properties' View group, or right-click the view and choose Rotate 90
  Anticlockwise or Rotate 90 Clockwise. Undo turns it back. The view turns
  about its centre, its sizes and notes turn with it and stay readable, and
  the DXF and PDF show it turned. The drawing keeps the turn when saved.
- The first command that needs a drawing's view regions, such as Drafting
  Pro's Balloon View, no longer waits several seconds: they are worked out
  while the drawing opens, and the window answers clicks all the while.

### Add-ons

- An add-on can put its commands on toolbars of its own, listed in View >
  Toolbars, and a toolbar can show only on the tabs it is for, a drafting
  add-on's only while a drawing is in front. Hidden that way, it stays
  ticked in View > Toolbars, which keeps your own choice.
- An add-on you downloaded twice, which the browser saved as `... (1).whl`,
  installs from Help > Add-ons > Install from File. What a wheel is built
  for is read from inside it, not from its file's name.
- Help > Add-ons shows the whole Licence text, "Free during your 30-day
  trial (ends ...)", with its date, on Windows, macOS and Linux.
- The SDK's plugin API is 5: an add-on's marks on a turned view turn with
  it.

### Install

- The macOS app is signed and notarised, so it opens without the "could not
  verify" box. For a build that is not, the install page gives macOS 15's
  way: System Settings > Privacy & Security, then Open Anyway.
- `dxcad serve --window` started before DX-CAD is open waits for the window
  instead of giving up, and says in its log why it stopped.

### Known limitations

- Those of 0.1.0, below, still hold.

## 0.1.2

An update to 0.1.1, 25 October 2026. It installs over 0.1.1, and your
files, settings and add-ons are kept; add-ons made for 0.1.1 work with it.

### Sheet metal

- Rounded slots, at any angle, through a sheet part's base or a flange's
  leg: draw one with the slot tool inside Base Flange's outline, type it on
  the Flange dialog's Slots line, or Cut one through a face, which keeps the
  part as sheet metal. The flat pattern and its DXF show each slot as two
  lines and two arcs, and the cut length counts them.

### Add-ons

- Installing or removing an add-on says so in a message box. Until you
  restart DX-CAD, the add-ons list shows a new version as "(after
  restart)", since the one running is still the old one.
- The add-ons are "Free during your 30-day trial", with the day it ends.
- Fabrication's shape dialogs and Drafting Pro's sheet tools work in the
  installed DX-CAD: it now carries every module an add-on may use. A sheet
  tool that cannot follow the mouse says so on the status bar.

### Licensing

- Licences (a paid subscription) are available from 1 November 2026. Until
  then, Help > Licence's Activate, Send code and Sign in say so and contact
  nothing; DX-CAD and its add-ons cost nothing until your trial ends. No
  trial ends before 16 November 2026.
- When the licence service cannot be reached, Help > Licence says so in one
  plain sentence.
- The Licence box shows every line in full and says each date once.
  Deactivate is greyed unless a licence is activated on this computer.

### Known limitations

- Those of 0.1.0, below, still hold.

## 0.1.1

An update to 0.1.0, 23 October 2026. It installs over 0.1.0, and your
files, settings and add-ons are kept.

### Modelling

- The Assistant reads the whole of your model.py, where the provider you
  chose has room for it, not only its first 6,000 characters.
- A long request to the Assistant, or a long reply, no longer makes the
  window wider than the screen. The Undo button says the start of a long
  answer's name; the Edit menu and the button's tooltip say all of it.

### Add-ons

- During your trial, the add-ons show in the menus and say where to
  download them; an add-on you have installed shows its menu once, with no
  greyed copy beside it.
- The SDK gives an add-on the licence words DX-CAD shows, with the trial's
  dates.

### Licensing

- Free for 30 days from first start, then a licence. Opening, viewing and
  exporting stay free. This plain 30-day trial replaces 0.1.0's offer; if
  you first started DX-CAD under 0.1.0, you keep the date 0.1.0's licence
  gave you, or your 30 days if they end later.
- The paid add-ons, Fabrication and Drafting Pro, are free during your
  trial too, while you hold no licence key.
- Activate and Deactivate never freeze the window, and a network failure
  is said in one plain line. A paid licence that has run out says so,
  rather than that the trial has ended.
- The licence is checked online every 8 hours while DX-CAD is open.
- Setting the computer's clock back does not unlock editing, a clock set
  ahead by mistake never locks it, and deleting DX-CAD's settings does not
  start the trial again.

### Install

- DX-CAD looks for a newer version as it starts and says so on the status
  bar; File > Settings switches that off.
- Windows Explorer shows thumbnails and icons for .dxcprt, .dxcasm and
  .dxcdrg files, and the installer replaces its thumbnail handler even
  while Explorer is using it.
- Double-clicking `dxcad.exe` says what it is and opens DX-CAD, and leaves
  no empty terminal window behind.
- Help > About shows every line at 200 percent display scaling.
- The macOS app is signed and notarised in the order Apple asks for, and
  the Linux wheel is one PyPI accepts.

### Known limitations

- Those of 0.1.0, below, still hold.

## 0.1.0

The first public release, 16 October 2026. Under its licence
([EULA.md](EULA.md)) as 0.1.0 shipped it, DX-CAD was free for any use, at
work too, until the date that licence gave, or until your 30-day trial ended
if that was later; 0.1.1 replaces this with a plain 30-day trial from first
start (see 0.1.1, above). After that, editing and saving need a licence;
opening, viewing and exporting your files stay free. Help >
Licence says where you stand. The SDK that add-ons are built on is open
source under Apache 2.0.

### Modelling

- Every part is a model.py you can read, change and run again. Boxes,
  cylinders, cones, spheres and tori; sketches extruded and revolved;
  fuse, cut and common; fillets, chamfers, holes, countersinks and
  counterbores; shells, lofts, sweeps, drafts, mirrors and patterns; and
  3D text, raised or cut. What you do in the window is written into the
  model as you do it.
- A sketcher with lines, rectangles, circles, arcs, polygons, slots,
  ellipses and splines, corner fillets and chamfers, offset, mirror, trim
  and break, sizes typed while you draw, and constraints.
- Parts, assemblies and drawings are three kinds of file (.dxcprt,
  .dxcasm, .dxcdrg), each in a tab of its own; tabs can be tiled side by
  side. Recent files, part colours, part numbers, revisions and your own
  properties.
- Assemblies: parts placed by numbers or by mates (coincident, concentric,
  distance, angle), parts used from their own files, sub-assemblies, a bill
  of materials and an interference check. Mates are suggested from
  matching features, and you confirm each one.
- Move a part by dragging it, hide and show parts, section the view with
  a cutting plane, and spin it on a turntable.
- Out to the shop: parts to STEP, STL, 3MF and BREP, flat patterns to DXF
  and SVG, a printability report, and Send to Slicer.
- An Assistant panel that builds and changes parts from what you type,
  with your own API key; each answer is one step of Undo.
- Autosave: after a crash, DX-CAD offers back what you had open.

### Sheet metal

- Base flanges from a closed sketch, arcs and circles included; flanges on
  any edge, on a flange's own edges too, with corners that never overlap;
  hems (open, closed and teardrop) and returns in or out at any angle.
- One dialog per command, with a diagram and a live preview. The Flange
  dialog takes all edges at once, or a length per edge in its table, and
  edits a flange you made before.
- Thickness, bend radius and K-factor from material and gauge tables.
- The flat pattern: Show Flat Pattern switches the view between formed
  and flat, with bend lines, the blank size, bend-line distances and a
  bend table; Export Flat Pattern writes DXF or SVG for a laser or a
  plasma table, with shop profiles, and `dxcad flat` writes the flat as a
  STEP solid too.

### Drawings

- A drawing is a document of its own, drawn again from its model whenever
  the model changes. Ten ISO and ANSI title blocks, on ISO sheets from A4
  to A0 and ANSI sheets A to D, fonts and text heights, linetypes.
- Front, top, right and isometric views, with hidden lines when you want
  them; Add View for any other, a view at a scale of its own, and Add Part
  Sheets for a sheet per part. Views move as you drag them and stay in
  line with the front unless you unlock them.
- Overall sizes, hole callouts and a parts list with item, part number,
  description, material, quantity and revision, and mass or size when you
  add those columns.
- Lines and polylines drawn by hand on the sheet.
- Out to PDF and DXF.
- Large assemblies (a hundred parts and more) open quickly on a drawing.

### Measure

- View > Measure: distance, angle, radius, diameter, length and area by
  picking points, edges and faces, in the 3D view, in a sketch and on a
  drawing. The status bar says what to pick next; the result shows beside
  the picks, on the status bar and in the Measure panel, with Copy.

### Add-ons

- Help > Add-ons... installs, lists, turns on and off and removes add-ons,
  from inside DX-CAD; installing a newer version over the old one updates
  it.
- DX-CAD Fabrication (cones, transitions, elbows, branches, weldments and
  more) and DX-CAD Drafting Pro (dimensions, balloons, tolerances, GD&T,
  section and detail views, revision tables and notes) are paid add-ons;
  every paid command shows in the menus, greyed, with its add-on's name.
  Both are unlocked, with no key, through your 30-day trial while you hold
  no licence; then each needs a
  licence of its own. Until an add-on is installed, its greyed commands and
  Help > Add-ons say where to download it while it is free, and where to
  buy it after that.
- An add-on brings its own menus, toolbar buttons, dialogs, drawing views
  and tools, and its own help: F1 in its command shows its steps. A command
  that does not apply to the tab in front is greyed, and its tooltip says
  why.
- Agents: `dxcad serve` is an MCP server, and Claude Desktop can drive the
  open window through it; Connect Claude Desktop sets it up in one click.
  Every operation is on the command line too.

### Install

- Windows: an installer, or a portable zip that needs no Python;
  both carry `dxcad.exe`, the command line.
- macOS (Apple silicon) and Linux (x64) builds.
- `pip install dxcad` on Python 3.12.
- `dxcad doctor` tells you the install works, ending with SMOKE OK, and
  `dxcad doctor --report` gives everything a bug report needs.
- A start page of example parts, six tutorials, and help on every command
  (F1, or the ? button in a dialog). How each build is installed and opened
  is in [docs/install.md](docs/install.md).

### Known limitations

- Add-on authors: `document.view_lines(view, parts="all")` names every part
  a drawn line lies on, but where one part is sunk inside another with no
  edge of its own on the line (the gearbox example's sight-glass lens in
  its bezel, a nameplate's letters in the plate) the hidden part is not
  named. `document.view_regions(view)` gives the part seen in each region
  of a view correctly, those included.
- STEP files keep assembly structure, names, colours, part numbers and
  properties, both ways; whether another CAD program shows those
  properties has not yet been checked.
- Pictures of DX-CAD files in Windows Explorer's large icons and preview
  pane have not yet been checked on a real desktop.
- The macOS and Linux builds come from CI and have not yet been run by
  hand. The macOS build is not yet signed by Apple; it opens as
  docs/install.md says.
- The Assistant's picture of the open window on macOS has not yet been
  checked by hand. On macOS a picture drawn with no window open
  (`dxcad render`, the agent's `render_view`) is refused, and a part saved
  there carries no preview picture.
- Mates are placed in order, one after another: there is no solver that
  moves parts together, and no joints or motion.
- What the kernel cannot do, and how DX-CAD says so, is in
  [docs/limitations.md](docs/limitations.md).
