proc parse_route {file_name} {

set file_id [open $file_name r+]
set file_data [read $file_id]
close $file_id

set file_id [open "$file_name-gMaps_track.txt" "w+" ]

set data [split $file_data "\n"]
set route "var routeCoordinates = \[\n"
set i 1
foreach line $data {
	if {($i>1) && ([expr $i%12]==0)} {
	    set files [split $line ","]
    	append route "new google.maps.LatLng([lindex $files 0],[lindex $files 1]),"
	}
	incr i
}
puts $i
append route "\n\];"
puts $file_id $route

close $file_id
}
