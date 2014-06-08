proc raam_parse_e {file_name} {

set file_id [open $file_name r+]
set file_data [read $file_id]
close $file_id

set file_id [open "$file_name-elev.txt" "w+" ]

set data [split $file_data "\n"]
set line_num 1
foreach line $data {
	if {[expr $line_num%200]==0 || $line_num==2} {
		puts -nonewline $file_id "$line|"
	}
	incr line_num
}
close $file_id
}