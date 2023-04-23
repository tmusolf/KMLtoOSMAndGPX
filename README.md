# KMLtoOSMAndGPX
Convert google my maps KML files to OSMAnd style GPX files, including icon conversion

Convert a KML file that was exported from google my maps into a GPX file in the 
format that OSMAnd understands.  This includes OSMAnd extensions and translation of
google waypoint icons into a similar OSMAnd icon.  Tracks and waypoints are the only
objects converted.

py KMLtoOSMAndGPX.py <input file> <output file> -l -w <width 1-24> -t <transparency 00 to FF> -s <split interval in miles>

You specify the input and output file names.
There are options to override the default track width and transparency values.
There is an option to specify the OSMAnd split interval, but when enabled, this feature
does not work as expected with multi-track GPX files. The interval mileage is additive 
across each track instead of resetting to mile 0 at the start of each track - makes it
pretty useless.  It does work for .

By default a single gpx file is created.  The -l option will create a separate GPX file
for each layer in the input KML file.  The output file value will then specify the path 
and base file name for these GPX files.  
The output GPX files for each layer will be named with the KML file name plus the layer name.
Any layer with a name in the LAYERS_TO_IGNORE list will not be processed.

Note: the KML tag name is "folder" and google my maps refers to them as "layers" so you'll see
references to both, they are the same thing.

You must import the file into OSMAnd, not copy the file into the Android/data/net.osmand.plus/files/tracks
directory.  When you My Places\+\Import Track you must select "import as one track".
This keeps all of the tracks and waypoints contained in the GPX file in that file. 
It also allows the track color and width "show start and finish icons" values in the file
to take effect.  If you modify any of the file's setting via OSMAnd you'll need to delete the
GPX file via OSMAnd to remove some "memory" that OSMAnd has.  If you don't modify any
file values via the app you can simply delete the files using any file manager app.

If you use the appearence function in OSMAnd to try and edit the color, line width
start/finish icon, split, arrows as soon as you enter this screen all of the track
color and transparency values contained in the file are set to whatever the current value is
in the appearance screen.  "Reset to original" does not reset the color and 
transparency values.  This doesn't seem like correct behavior in OSMAnd

It is unfortunate that OSMAnd does not allow each track in an imported GPX file to
have it's attributes (color, width, transparency, arrows, start/stop, split)
independenlty managed.  In addition, the <desc> tag is ignored both in the main <trk>
tag and also in <extensions>.  The only <desc> that is used is one for the entire
file contained in the <metadata><extensions> tag.

If the GPX file has more than 2 and 50 or less tracks you will be given the option to
import the GPX file as separate tracks. OSMAnd creates separate gpx files, one
for each track.  It suggests which icons to place in each gpx file based on the distance
the waypoints are from the track.  All the waypoints will be covered and you can adjust
these suggestions if you desire.  The problem with this approach is that track colors
and transparency values are igonored.  I believe OSMAnd uses the values from the <extensions>
tags at the <gpx> level, not the track level.

At this point there is minimal error checking in the code.
