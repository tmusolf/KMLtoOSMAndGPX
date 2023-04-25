#!/usr/bin/python
#========================================================================================
# Convert a KML file that was exported from google my maps into a GPX file in the 
# format that OSMAnd understands.  This includes OSMAnd extensions and translation of
# google waypoint icons into a similar OSMAnd icon.  Tracks and waypoints are the only
# objects converted.
#
# You specify the input and output file names.
# There are options to override the default track width and transparency values.
# There is an option to specify the OSMAnd split interval, but when enabled, this feature
# does not work as expected with multi-track GPX files. The interval mileage is additive 
# across each track instead of resetting to mile 0 at the start of each track - makes it
# pretty useless.  It does work for .
#
# By default a single gpx file is created.  The -l option will create a separate GPX file
# for each layer in the input KML file.  The output file value will then specify the path 
# and base file name for these GPX files.  
# The output GPX files for each layer will be named with the KML file name plus the layer name.
# Any layer with a name in the LAYERS_TO_IGNORE list will not be processed.
#
# Note: the KML tag name is "folder" and google my maps refers to them as "layers" so you'll see
# references to both, they are the same thing.
#
# You must import the file into OSMAnd, not copy the file into the Android/data/net.osmand.plus/files/tracks
# directory.  When you My Places\+\Import Track you must select "import as one track".
# This keeps all of the tracks and waypoints contained in the GPX file in that file. 
# It also allows the track color and width "show start and finish icons" values in the file
# to take effect.  If you modify any of the file's setting via OSMAnd you'll need to delete the
# GPX file via OSMAnd to remove some "memory" that OSMAnd has.  If you don't modify any
# file values via the app you can simply delete the files using any file manager app.
#
# If you use the appearence function in OSMAnd to try and edit the color, line width
# start/finish icon, split, arrows as soon as you enter this screen all of the track
# color and transparency values contained in the file are set to whatever the current value is
# in the appearance screen.  "Reset to original" does not reset the color and 
# transparency values.  This doesn't seem like correct behavior in OSMAnd
#
# It is unfortunate that OSMAnd does not allow each track in an imported GPX file to
# have it's attributes (color, width, transparency, arrows, start/stop, split)
# independenlty managed.  In addition, the <desc> tag is ignored both in the main <trk>
# tag and also in <extensions>.  The only <desc> that is used is one for the entire
# file contained in the <metadata><extensions> tag.
#
# If the GPX file has more than 2 and 50 or less tracks you will be given the option to
# import the GPX file as separate tracks. OSMAnd creates separate gpx files, one
# for each track.  It suggests which icons to place in each gpx file based on the distance
# the waypoints are from the track.  All the waypoints will be covered and you can adjust
# these suggestions if you desire.  The problem with this approach is that track colors
# and transparency values are igonored.  I believe OSMAnd uses the values from the <extensions>
# tags at the <gpx> level, not the track level.
#
# At this point there is minimal error checking in the code.
#
# 4/23/2023: V2.1 Tom Musolf with a little amazing help from ChatGPT
# 4/25/2023: V2.2 If you export a single layer/folder from your google my map it is not
#	put into a folder.  Current code does not check for no folders and only processes
#	tracks and waypoint contained in folders.  So there needs to be special case added
#	to handle the no folder case.  If you have a map with a single layer and export the
#	entire map that single layer will be contained in a folder - so no issues with this case.
#	Also added and display counts for waypoint, tracks and folders.
#	Moved waypoint and track processing code into functions so it can be used again
#	in no folder case.
#========================================================================================
import argparse
import xml.etree.ElementTree as ET
from xml.dom import minidom
import ntpath

PROGRAM_VERSION = "2.2"
DEFAULT_TRACK_TRANSPARENCY = "80"
DEFAULT_TRACK_WIDTH = "14"
# Both of these should probably be command line arguments
DEFAULT_TRACK_COLOR = "3AE63A"  # a kelley green color
DEFAULT_ICON_COLOR = "DB4436"	# rusty red
DEFAULT_TRACK_SPLIT = "no_split"
KMLCOLOR = "KMLCOLOR"
# Probably should make this a command line arguent
LAYERS_TO_IGNORE = ["Untitled layer"]

# globals to keep track of some counts
countFolders = 0
countFolderWaypoints = 0
countFolderTracks = 0
countTotalWaypoints = 0
countTotalTracks = 0

#========================================================================================
#========================================================================================
class cWaypoint:
	def __init__ (self,icon,color,background):
		self.icon = icon
		self.color = color
		self.background = background

#========================================================================================
# iconDictionary describes the mapping between a KML icon number and an OSMAnd icon name.
# It also contains a default OSMAnd color and shape to use for each OSMAnd icon type.
# 
# iconDictionary format:
# 	"KML icon number":["OSMAnd Icon name","HTML hex color code or flag to use KMLCOLOR","OSMAnd shape"]
# 
# Color code is a standard 6 digit HTML hex color code.  This is what OSMAnd uses
# 	Put the string "KMLCOLOR", without the double quotes, in for a color value if you want to use the color specified in the KML file
# 	for a particular icon.
# As of 8/2020 OSMAnd icons do not support transparent colors.
# As of 8/2020 OSMAnd supports 3 icon shapes: circle, octagon, square
# 
# To add additional KML icons to the dictionary.
#
# For each icon you want to translate you need to add a new entry/line into the iconDictionary table. 
# To determine what the KML and OSMAnd icons are you want go through the following steps:
#
# KML icon number
# 	1) Create a google my maps test file with the icons you want to use.
# 	2) Export this map as a KML file.  
# 	3) Open up the file in a text editor and look for your points. You can ignore all the <style> & <StyleMap> tags at the 
#	   beginning of the KML file.  The points/waypoints/Placemarks will look like this:
#
#		<Placemark>
#			<name>Mileage Marker dot</name>
#			<styleUrl>#icon-1739-0288D1-nodesc</styleUrl>
#			<Point>
#				<coordinates>-120.8427259,38.8170119,0</coordinates>
#			</Point>
#		</Placemark>

# The <styleUrl> tag has the icon number.  In the preceeding example it's "1739".
#
# OSMAnd Icon name
#	1) Create some favorites using the icons you want.
#	2) Goto .../Android/data/net.osmand.plus/files/favorites/favorites.gpx
#	3) Open the favorites file in a text editor and look for the waypoints.
#	   in the following example the icon name is: "special_trekking"
#
#		<wpt lat="39.2906659" lon="-121.4965106">
#			<name>hiker, pale yellow</name>
#			<extensions>
#			<color>#eeee10</color>
#			<icon>special_trekking</icon>
#			<background>circle</background>
#			</extensions>
#		</wpt>
#========================================================================================
def KMLToOSMAndIcon(KMLIconID):

	iconDictionary ={
		"unknown":["special_symbol_question_mark","e044bb","octagon"],			#unknown KML icon code - this entry will be used if the KML icon is not found the iconDictionary.
		"1765":["tourism_camp_site",KMLCOLOR,"circle"],							#campsite
		"1525":["leisure_marina","a71de1","octagon"],							#river access
		"1739":["special_number_0",KMLCOLOR,"circle"],							#Mileage marker plus-KML dot on gmaps & Plus in OSMAnd. Did have this color:"1010a0"
		"1596":["special_trekking",KMLCOLOR,"circle"],							#hiking trailhead  Color I use is 9E963A
		"1369":["special_trekking",KMLCOLOR,"circle"],							#hiking trailhead -old style icon
		"1371":["special_trekking",KMLCOLOR,"circle"],							#hiking trailhead -old style icon
		"1723":["tourism_viewpoint",KMLCOLOR,"octagon"],						#rapid  "d90000"
		"1602":["tourism_hotel",KMLCOLOR,"circle"],								#hotel, lodge
		"1528":["bridge_structure_suspension","10c0f0","circle"],				#bridge
		"1577":["restaurants",KMLCOLOR,"circle"],								#retaurant, diner, dining
		"1085":["restaurants",KMLCOLOR,"circle"],								#retaurant, diner, dining, old style icon
		"1650":["tourism_picnic_site","eecc22","circle"],						#picnic site
		"1644":["amenity_parking",KMLCOLOR,"circle"],							#parking area
		"1578":["shop_supermarket",KMLCOLOR,"circle"],							#grocery store, supermarket #1 - light blue "10c0f0"
		"1685":["shop_supermarket",KMLCOLOR,"circle"],							#grocery store, supermarket #2 - light blue	"10c0f0"
		"1023":["shop_supermarket",KMLCOLOR,"circle"],							#grocery store, supermarket #2 - light blue	"10c0f0", old style grocery icon
		"1504":["air_transport","10c0f0","circle"],								#airport, airstrip
		"1581":["fuel",KMLCOLOR,"circle"],										#gas station
		"1733":["amenity_toilets","10c0f0","circle"],							#toilet, restroom
		"1624":["amenity_doctors","d00d0d","circle"],							#hospital, doctor, emergency room
		"1608":["tourism_information","1010a0","circle"],						#tourism information
		"1203":["tourism_information","1010a0","circle"],						#tourism information, old style icon - big "i"
		"1535":["special_photo_camera",KMLCOLOR,"circle"],						#POI #1, camera "eecc22"
		"993": ["special_photo_camera",KMLCOLOR,"circle"],						#POI #1, camera "eecc22" old icon style
		"1574":["special_flag_start",KMLCOLOR,"circle"],						#POI #2, flag "eecc22"
		"1899":["special_marker",KMLCOLOR,"circle"],							#POI #3, pin "eecc22"
		"1502":["special_star",KMLCOLOR,"circle"],								#POI #4, star "eecc22"
		"1501":["special_symbol_plus",KMLCOLOR,"circle"],						#POI #5, plus/diamond "eecc22"
		"1500":["special_flag_start",KMLCOLOR,"circle"],						#POI #6, square in google maps & square flag i OSMAnd
		"1592":["special_heart",KMLCOLOR,"circle"],								#POI #7, heart
		"1729":["tourism_viewpoint",KMLCOLOR,"circle"],							#Vista point / viewpoint
		"503": ["special_marker",KMLCOLOR,"circle"],							#Old school map point
		"1603":["special_house","eecc22","circle"],								#house
		"1879":["amenity_biergarten",KMLCOLOR,"circle"],						#brewery, brew pub
		"1541":["special_symbol_exclamation_mark","ff0000","octagon"],			#danger #1 GMaps: "!" 		OSMAnd: exclamation
		"1898":["special_symbol_exclamation_mark",KMLCOLOR,"octagon"],			#danger #1 GMaps: "X" 		OSMAnd: exclamation 
		"1564":["amenity_fire_station","ff0000","octagon"],						#danger #2 GMaps: 			OSMAnd: fire/explosion
		"1710":["special_arrow_up_and_down","10c0f0","circle"],					#river gauge, up/down arrow or thermometer
		"1655":["amenity_police","1010a0","circle"],							#ranger/police station #1
		"1657":["amenity_police","1010a0","circle"],							#ranger/police station #2
		"1720":["wood","eecc22","circle"],										#Park/National Park - yellow
		"1701":["sport_swimming","eecc22","circle"],							#Lake/swimmer - yellow
		"1395":["sport_swimming","eecc22","circle"],							#Lake/swimmer - yellow, old style icon
		"1811":["special_sun","eecc22","circle"],								#hot spring/sun - yellow
		"1716":["route_railway_ref",KMLCOLOR,"circle"],							#train station - purple
		"1532":["route_bus_ref",KMLCOLOR,"circle"],								#bus station or stop
		"1626":["route_monorail_ref",KMLCOLOR,"circle"],						#Metro, subway stop
		"1534":["amenity_cafe",KMLCOLOR,"circle"],								#cafe/coffe - blue
		"1607":["amenity_cafe",KMLCOLOR,"circle"],								#cafe/coffe - blue, old style ice cream cone icon
		"1892":["waterfall","eecc22","circle"],									#waterfall - yellow
		"1634":["building_type_pyramid","eecc22","circle"],						#Mountain Peak - yellow
		"1684":["shop_department_store","10c0f0","circle"],						#Store/shopping - blue
		"1095":["shop_department_store","10c0f0","circle"],						#Store/shopping - blue	old style shopping icon
		"1517":["amenity_bar",KMLCOLOR,"circle"],								#Bar/cocktails/lounge - blue, old style icon
		"979": ["special_sail_boat","a71de1","circle"],							#Passenger ferry - purple
		"1537":["special_sail_boat",KMLCOLOR,"circle"],							#Auto Ferry
		"1498":["place_town","0244D1","circle"],								#town/city/village - Google circle with small square in center
		"1521":["leisure_beach_resort","eecc22","circle"],						#beach - yellow
		"1703":["amenity_drinking_water","00842b","circle"],					#Water Faucet - green
		"1781":["sanitary_dump_station","10c0f0","circle"],						#RV Dump station - light blue
		"1798":["Winery",KMLCOLOR,"circle"],									#Winery - light blue
		"1636":["Museum",KMLCOLOR,"circle"],									#Museum - light blue
		"1289":["Museum","10c0f0","circle"],									#Museum - light blue, old style icon
		"1741":["special_wagon","10c0f0","circle"],								#car rental - light blue
		"1590":["shop_car_repair","10c0f0","circle"],							#car/tire repair - light blue
		"1659":["amenity_post_box","10c0f0","circle"],							#post office
		"1512":["amenity_atm","10c0f0","circle"],								#bank/atm
		"1870":["sport_scuba_diving",KMLCOLOR,"octagon"],						#scuba, dive, snorkel site, google maps - snorkel mask, OSMAnd scuba diver
		"1882":["reef",KMLCOLOR,"octagon"],										#reef, tide pool - google maps starfish icon, OSMAnd seahorse/coral
		"1573":["reef",KMLCOLOR,"octagon"],										#reef, tide pool, fishing spot - google maps fish icon, OSMAnd seahorse/coral
		"1569":["special_sail_boat",KMLCOLOR,"circle"],							#Passenger Ferry
		"1741":["special_wagon",KMLCOLOR,"circle"],								#Car Rental
		"1538":["special_wagon",KMLCOLOR,"circle"],								#Car Rental
		"1709":["amenity_cinema",KMLCOLOR,"circle"],							#Cinema, movie, theater
		"1615":["sport_canoe",KMLCOLOR,"circle"],								#Kayak, kayak rental
		"1598":["historic_castle",KMLCOLOR,"circle"],							#castle, ruins
		"1670":["building_type_church",KMLCOLOR,"circle"],						#church, mosque, temple
		"1877":["special_arrow_up_arrow_down",KMLCOLOR,"circle"],				#stairway, for OSMAnd it's up/down arrow icon
	}
	
	waypt = cWaypoint("unknown",KMLCOLOR,"circle")

	if not KMLIconID in iconDictionary:
		KMLIconID = "unknown"
	waypt.icon = iconDictionary[KMLIconID][0]
	if iconDictionary[KMLIconID][1] == KMLCOLOR:
		#use the icon color from the KML file
		waypt.color = KMLCOLOR
	else:
		#use the icon color from the dictionary table
		waypt.color = iconDictionary[KMLIconID][1]
	waypt.background = iconDictionary[KMLIconID][2]
	#print("icon:", waypt.icon, "color:", waypt.color, "background:",waypt.background)
	return(waypt)
#========================================================================================
# addFileExtensionsTags
#========================================================================================
def addFileExtensionsTags(gpx,args):
	# add extensions that apply to all tracks
	# seems like this should be at the track level, but it's not
	extensions = ET.SubElement(gpx,"extensions")
	if args.width:
		ET.SubElement(extensions, "width").text = str(args.width)
	else:
		ET.SubElement(extensions, "width").text = DEFAULT_TRACK_WIDTH
	ET.SubElement(extensions, "show_arrows").text = "false"
	ET.SubElement(extensions, "show_start_finish").text = "false"
	# When you have multiple tracks in a file the split amounts are cummulative across
	# all the tracks. Each track's split values don't start at zero.
	if args.split == DEFAULT_TRACK_SPLIT:
		ET.SubElement(extensions, "split_type").text = DEFAULT_TRACK_SPLIT
	else:
		ET.SubElement(extensions, "split_type").text = "distance"
		#split interval is in meters and args.interval is in miles, so convert miles to meters
		ET.SubElement(extensions, "split_interval").text = str(int(float(args.split) * 1609.34))
	return
#========================================================================================
# writeGPXFile
#========================================================================================
def writeGPXFile(gpx,outputFilename):
	# Create the ElementTree object with pretty printing options
	tree = ET.ElementTree(gpx)
	tree_str = ET.tostring(gpx, encoding="utf-8", xml_declaration=True)
	pretty_tree_str = minidom.parseString(tree_str).toprettyxml(indent="  ", encoding="utf-8").decode()

	# Write the pretty-printed GPX XML to a file
	with open(outputFilename, "w",encoding="utf-8") as f:
		f.write(pretty_tree_str)
#========================================================================================
# processWaypoint
#========================================================================================
def processWaypoint(placemark,gpx):
	global countFolderWaypoints
	global countTotalWaypoints
	# Get the coordinates from the KML Point element
	point = placemark.find(".//{http://www.opengis.net/kml/2.2}Point/{http://www.opengis.net/kml/2.2}coordinates")
	if point is not None:
		countFolderWaypoints += 1
		countTotalWaypoints += 1
		coordinates = point.text.strip().split(",")
		longitude = coordinates[0]
		latitude = coordinates[1]
		elevation = coordinates[2]
		#print("long",longitude, "lat",latitude,"elev",elevation)

		# Create the GPX Waypoint element
		waypoint = ET.SubElement(gpx, "wpt", lat=latitude, lon=longitude)
		# Add the name and description from the KML Placemark element, if available

		name = placemark.find(".//{http://www.opengis.net/kml/2.2}name")
		if name is not None:
			name = name.text.strip()
			print("      WayPt:",name)
			ET.SubElement(waypoint, "name").text = name

		description = placemark.find(".//{http://www.opengis.net/kml/2.2}description")
		if description is not None:
			description = description.text.strip()
			ET.SubElement(waypoint, "desc").text = description

		# add elevation
		ET.SubElement(waypoint,"ele").text = elevation

		# add extensions
		extensions = ET.SubElement(waypoint,"extensions")
		# Use styleURL tag value to extract color and icon ID
		# New icons appear to be of this style with an icon ID and a color
		#	<styleUrl>#icon-1577-DB4436-labelson</styleUrl>
		# Old style icons come in two flavors, neither of which has color info
		#	<styleUrl>#icon-1369</styleUrl>
		#	<styleUrl>#icon-1085-labelson</styleUrl>
		#
		# if there is no color field (get an exception on trying to access the field)
		# then we will use the DEFAULT_ICON_COLOR value.  If the second field contains
		# the string "labelson" we'll also use the DEFAULT_ICON_COLOR value.
		style_url = placemark.findtext(".//{http://www.opengis.net/kml/2.2}styleUrl")
		if style_url:
			style = style_url.split("-")
			waypt = KMLToOSMAndIcon(style[1])
		else:
			waypt = KMLToOSMAndIcon("unknown")
		#print("KMLToOSMAndIcon: icon:",waypt.icon,"color:",waypt.color,"background:",waypt.background)
		ET.SubElement(extensions,"icon").text = waypt.icon
		ET.SubElement(extensions,"background").text = waypt.background
		if waypt.color == KMLCOLOR: # we use value from KML file
			try:
				if style[2] == "labelson":  # there is no color value in styleURL string
					waypt.color = DEFAULT_ICON_COLOR
				else:
					waypt.color=style[2]
			except IndexError:
				waypt.color=DEFAULT_ICON_COLOR
		ET.SubElement(extensions, "color").text = "#" + waypt.color
#========================================================================================
# processTrack
#========================================================================================
def processTrack(placemark,gpx,args):
	global countFolderTracks
	global countTotalTracks
	# Get the coordinates from the KML LineString element
	linestring = placemark.find(".//{http://www.opengis.net/kml/2.2}LineString/{http://www.opengis.net/kml/2.2}coordinates")
	if linestring is not None:
		countFolderTracks += 1
		countTotalTracks += 1
		# Create the GPX Track element with the trackpoints
		track = ET.Element("trk")
		# Add the name and description from the KML Placemark element, if available
		name = placemark.find(".//{http://www.opengis.net/kml/2.2}name")
		if name is not None:
			name = name.text.strip()
			print("      Track:",name)
			ET.SubElement(track, "name").text = name

		description = placemark.find(".//{http://www.opengis.net/kml/2.2}description")
		if description is not None:
			description = description.text.strip()
			ET.SubElement(track, "desc").text = description

		coordinates = linestring.text.strip().split()
		trackpoints = []
		trkseg = ET.SubElement(track, "trkseg")
		# Iterate over the coordinates and create GPX trackpoints
		for coordinate in coordinates:
			longitude, latitude, altitude = coordinate.split(",")
			trackpoint = ET.Element("trkpt", lat=latitude, lon=longitude)
			if altitude is not None:
				ET.SubElement(trackpoint, "ele").text = altitude
			trackpoints.append(trackpoint)
		for trackpoint in trackpoints:
			trkseg.append(trackpoint)

		extensions = ET.SubElement(track,"extensions")

		#              [0]   [1]    [2]
		#                    color width
		#   <styleUrl>#line-0F9D58-1000</styleUrl>
		#Color is standard RGB color with no transparency
		#Line width is 1000-32000.  This maps to 1.0-24.0 for OSMAnd line width
		style_url = placemark.findtext(".//{http://www.opengis.net/kml/2.2}styleUrl")
		if style_url:
			style = style_url.split("-")
			color = style[1]
			#print("track color:",color)
		else:
			color = DEFAULT_TRACK_COLOR
		if args.transparency:
			transparency = args.transparency
		else:
			transparency = DEFAULT_TRACK_TRANSPARENCY
		ET.SubElement(extensions, "color").text = "#" + transparency + color
		
		#Seems like the <extensions> for track width, show_arrows and split 
		#should be associated with each track, but OSMAnd doesn't do it that way, it's file based
		#If track level was supported the code to write those extensions tags would be moved here.
		#
		# To scale the width range of 1000-32000 from the KML file to a range of 1-24
		# for OSMAnd in the gpx file, you can use the following formula:
		#		y = ((x - 1000) / 31000) * 23 + 1
		#		Where:
		#			x is the value in the original KML range of 1000-32000
		#			y is the scaled value in the GPX range of 1-24

		# Add the GPX Track element to the GPX file
		gpx.append(track)
#========================================================================================
# Main
#========================================================================================
def main():
	global countFolders
	global countFolderTracks
	global countFolderWaypoints
	global countTotalTracks
	global countTotalWaypoints
	# Parse the command line arguments
	parser = argparse.ArgumentParser(
	prog="v2",
	description="Convert KML waypoints and tracks to GPX",
	epilog="text at bottom of help")
	parser.add_argument("kml_file",
		help="the input KML file path/name")
	parser.add_argument("gpx_file", 
		help="the output GPX file path/name or if the -l option is specifed this is the path and output file(s) name prefix")
	parser.add_argument('-l', '--layers', 
		action='store_true', 
		default=False,
		help='False (default): A single GPX file is created.  True: The tracks & waypoints in each KML layer will be written to a separate GPX file.')
	parser.add_argument('-t', '--transparency', 
		action='store', 
		default=DEFAULT_TRACK_TRANSPARENCY,
		help='Transparency value to use for all tracks.  Specified as a 2 digit hex value.  00 is fully transparent and FF is opaque.')
	parser.add_argument('-s', '--split', 
		action='store',
		default=DEFAULT_TRACK_SPLIT, 
		help='Display distance splits along tracks. Value is in miles. Between 0.0 and 100.0')
	parser.add_argument('-w', '--width', 
		action='store', 
		default=DEFAULT_TRACK_WIDTH,
		type=int,
		help='Width value to use for all tracks. Integer value between 1-24')
	args = parser.parse_args()
	print("")
	print("KML to OSMAnd GPX file conversion")
	print("  Version:" + PROGRAM_VERSION)
	print("  Input file:        ", args.kml_file)
	print("  Output file:       ", args.gpx_file)
	print("  Output file path:  ", ntpath.dirname(args.gpx_file))
	print("  Output file name:  ", ntpath.basename(args.gpx_file))
	print("  Layer flag:        ", args.layers)
	print("  Transparency value: 0x", args.transparency)
	print("  Track width:       ", args.width)
	print("  Track split:       ", args.split)
	print("")
	print("Starting conversion...")

	# Parse the KML file
	tree = ET.parse(args.kml_file)
	root = tree.getroot()
	# Create the GPX root element if the -l option is specified we'll do this for each folder
	gpx = ET.Element("gpx", version="1.1", xmlns="http://www.topografix.com/GPX/1/1")

	# process the KML file a folder at a time.  If the -l flag is specified each folder's data
	# will get written to a separate GPX file.  If the -l flag is not specifgied than all
	# the data is saved up and written to a single file.

	#Note: the iter() function returns an iterator.  There appears to be no clean way to
	#check if the iterator is empty without using the first element.  The countFolders value
	#is used at the end of the folder for loop to see if any folders were processed.  If not,
	#then waypoints and tracks are processed at the root level instead of <folders> level.

	folders = root.iter('{http://www.opengis.net/kml/2.2}Folder')
	for folder in folders:
		# Extract the folder name from the KML file
		folder_name = folder.find('{http://www.opengis.net/kml/2.2}name').text
		print("")
		if folder_name in LAYERS_TO_IGNORE:
			print("Skipping layer:", folder_name)
			continue
		print("Processing layer:",folder_name)
		countFolders += 1
		#------------------------------------------------------------------------------------
		# Convert the waypoints from the KML file
		#------------------------------------------------------------------------------------
		for placemark in folder.findall(".//{http://www.opengis.net/kml/2.2}Placemark"):
			processWaypoint(placemark,gpx)
		#------------------------------------------------------------------------------------
		# Convert the tracks from the KML file
		#------------------------------------------------------------------------------------
		for placemark in folder.findall(".//{http://www.opengis.net/kml/2.2}Placemark"):
			processTrack(placemark,gpx,args)
		print("   Waypoint count:", countFolderWaypoints)
		countFolderWaypoints = 0
		print("   Track count:   ", countFolderTracks)
		countFolderTracks = 0
		#Done processing a folder
		#If the layers command line switch was specified then we write out each folder
		#as a separate GPX file.
		if args.layers:
			outputFilename = ntpath.join(ntpath.dirname(args.gpx_file),ntpath.basename(args.gpx_file) + "-" + folder_name + ".gpx")
			print("Writing GPX output file for layer:",folder_name,"to file:",outputFilename)
			addFileExtensionsTags(gpx,args)
			writeGPXFile(gpx,outputFilename)
			# Create the GPX root element if the -l option is specified we'll do this for each folder
			gpx = ET.Element("gpx", version="1.1", xmlns="http://www.topografix.com/GPX/1/1")
	#processed all folders, but if it was a single layer export from google maps there will be 
	#no folders, just waypoint and tracks at the <document> level. 
	if countFolders == 0:
		print("")
		print("No folders found")
		#------------------------------------------------------------------------------------
		# Convert the waypoints from the KML file
		#------------------------------------------------------------------------------------
		for placemark in root.findall(".//{http://www.opengis.net/kml/2.2}Placemark"):
			processWaypoint(placemark,gpx)
		#------------------------------------------------------------------------------------
		# Convert the tracks from the KML file
		#------------------------------------------------------------------------------------
		for placemark in root.findall(".//{http://www.opengis.net/kml/2.2}Placemark"):
			processTrack(placemark,gpx,args)
		print("   Waypoint count:", countFolderWaypoints)
		countFolderWaypoints = 0
		print("   Track count:   ", countFolderTracks)
		countFolderTracks = 0
		
	print("")
	print("   Total waypoint count:", countTotalWaypoints)
	print("   Total track count:   ", countTotalTracks)
	print("   Total folder count:  ", countFolders)

	#Done processing the file and if we are not writing individual folder/layer
	#files then write out the one and one gpx file.
	#There's a corner case here if there are no folders and the -l (layers) flag
	#was specified.  Could either not write out any data because there are no layers
	#or write a single file - which is what we do here.
	if (countFolders == 0) or (not args.layers):
		print("Writing single GPX output file:",args.gpx_file)
		addFileExtensionsTags(gpx,args)
		writeGPXFile(gpx,args.gpx_file)

if __name__ == "__main__":
	main()