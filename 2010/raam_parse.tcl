proc raam_parse {file_name} {

set file_id [open $file_name r+]
set file_data [read $file_id]
close $file_id

set file_id [open "$file_name-arrays.txt" "w+" ]

set data [split $file_data "\n"]
set route "var RAAMline = new GPolyline(\[\n"
set i 1
foreach line $data {
	if {$i>1} {
	    set files [split $line ","]
    	append route "new GLatLng([lindex $files 0],[lindex $files 1]),"
	}
	incr i
}
append route "\n\], \"#ff0000\", 2);"
puts $file_id $route

close $file_id
}