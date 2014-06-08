proc raam_parse_time {file_name} {

set file_id [open $file_name r+]
set file_data [read $file_id]
close $file_id

set file_id [open "$file_name-swap.txt" "w+" ]

set data [split $file_data "\n"]
set lat "var lat=\["
set lng "var lng=\["
set notes "var notes=\["
foreach line $data {
	set files [split $line ","]
	append lat "\"[lindex $files 0]\","
	append lng "\"[lindex $files 1]\","
	append notes "\"[lindex $files 2]\","
}
append lat "\];"
append lng "\];"
append notes "\];"
puts $file_id $lat
puts $file_id $lng
puts $file_id $notes

close $file_id
}