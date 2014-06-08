proc parse_timestations {file_name} {

set file_id [open $file_name r+]
set file_data [read $file_id]
close $file_id

set file_id [open "$file_name-gMaps_time_stations.txt" "w+" ]

set data [split $file_data "\n"]
set TSs "var timestations = {};\n"

foreach line $data {
	set files [split $line ","]
	append TSs "timestations\[\'[lindex $files 2]\'\] = {position: new google.maps.LatLng([lindex $files 0], [lindex $files 1])};\n"
}

puts $file_id $TSs

close $file_id
}