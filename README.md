# KMLtoOSMAndGPX
Convert google my maps KML files to OSMAnd style GPX files, including icon conversion.

Convert a KML file that was exported from google my maps into a GPX file. This includes OSMAnd extensions and translation of google waypoint icons into a similar OSMAnd icon.  Tracks and waypoints are the only objects converted.  Folders/layers are used as described below.
## Syntax
```
py KMLtoOSMAndGPX.py <input file> <output file> -l -w <width 1-24> -t <transparency 00 to FF> -s <split interval in miles>
``` 
Parm | Long Parm | Description
--- | --- | ---
kml_file | | Input KML file path/name. Required
gpx_file | | Output GPX file path/name or if the -l option is specifed this is the path and output file(s) name prefix. Required
-l | --layers | If present, the tracks & waypoints in each KML layer will be written to a separate GPX file. If abscent, output is to a single file.
-t | --transparency | Transparency value to use for all tracks.  Specified as a 2 digit hex value without the preceeding "0x".  00 is fully transparent and FF is opaque.
-s | --split | Display distance splits along tracks. Value is in miles. Between 0.0 and 100.0 Note: there is an OSMAnd issue with this feature in GPX files containing multiple tracks.
 -w | --width Width | All tracks will be rendered using this line width value. Integer value between 1-24

## KML folders and layers
The KML tag name is "folder" and google my maps refers to them as "layers" so you'll see
references to both, they are the same thing.

## Using GPX files with OSMAnd
You must import the GPX files into OSMAnd, not copy the file into the Android/data/net.osmand.plus/files/tracks directory.  You must select "import as one track" in order to keep all of the tracks and waypoints together in a single, imported, GPX file. 

Keeping the tracks and waypoints together in a single file allows the track color to be specified independently for each track.  The track line width, "show start and finish icons" and "arrow" values apply to all tracks in the file.

If the GPX file has more than 2 and 50 or less tracks OSMAnd offers the option to import the GPX file as separate tracks. OSMAnd will create separate gpx files, one for each track.  It suggests which waypoints to place in each gpx file based on the distance the waypoints are from the track.  All the waypoints will be covered and you can adjust these suggestions if you desire. Files are names using the track `<name>` tag.

The problem with the separate file approach is that track colors and transparency values are igonored by OSMAnd.  I believe OSMAnd uses the values from the `<extensions>` section at the `<gpx>` tag level, instead of the track level.

If you use the appearence function in OSMAnd to try and edit the color, line width start/finish icon, split, arrows as soon as you enter this screen the track color and transparency values for all tracks in the file are set the current appearance screen values. "Reset to original" does not reset the color and transparency values.  This doesn't seem like correct behavior in OSMAnd

To remove the imported GPX files from OSMAnd you can either delete them using a file manager from the location they were imported into or use the OSMAnd appearance delete function.  If you modify any of the file's setting via the OSMAnd appearance screen you'll need to delete the GPX file via OSMAnd delete function in order to remove some "memory" that OSMAnd apparantly has. 

It is unfortunate that OSMAnd does not allow each track in an imported multitrack GPX file to have it's attributes (color, width, transparency, arrows, start/stop, split) independenlty managed.

OSM ignores the `<desc>` tag contained in the `<trk>` section for each track and also the `<desc>` tag at the `<trk><extensions>` level.  The only `<desc>` tag used by OSMAnd is from `<metadata><extensions>`.

When used with GPX files containing multiple tracks there is an issue with how OSMAnd handles the splits.  The interval mileage is additive acrross each of the tracks in the GPX file instead of resetting it to mile 0 at the start of each track.  This behavior doesn't make it very useful in cases, such as multiple hiking trails in a file, where you want to see the interval distance from the start of each trail.

## Parting words
This is a work in progress. I'm not python guru so the code structure is probably not totally pythonic. At this point there is minimal error checking in the code.
