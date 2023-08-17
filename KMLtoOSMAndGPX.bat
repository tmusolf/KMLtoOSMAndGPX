@echo off
echo.
echo Batch file to run KMLtoOSMAndGPX.py which will convert 
echo google maps KML files into a GPX file for OSMAnd.
echo Utility uses an icon translation table to translate a known set
echo of KML icons into OSMAnd icons.
echo.
set pyprogram="KMLtoOSMAndGPX.py"
if exist %pyprogram% goto getinput
echo ***Python program not found***
echo Update the pyprogram variable in this batch file to be the fully qualified path and file name for 
echo the KMLtoOSMAndGPX.py program
echo.
goto end
:getinput
set /p file= "Enter KML base file name without path and .KML extension (assumes download dir): "
set infile="C:\Users\%USERNAME%\Downloads\%file%.kml"
set outfile="C:\Users\%USERNAME%\Downloads\%file%.gpx"
echo Input file: %infile%
echo Output file: %outfile%

if exist %infile% goto execute 
echo.
echo ***Missing input file: %infile% ***
echo.
goto end
:execute
REM Change this path to point to location of KMLtoOSMAndGPX.py program
py %pyprogram% %infile% %outfile%
:end
echo.
echo Done
pause
