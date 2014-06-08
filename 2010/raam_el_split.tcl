proc raam_el_split {file_name} {
	set file_id [open $file_name "r"]
	set file_data [read $file_id]
	close $file_id

	set file_id [open "$file_name-split.txt" "w+" ]

	set data [split $file_data " "]
	set i 1
	foreach value $data {
    	if {[expr $i%3]==0} {
        	puts -nonewline $file_id "[format %.5s [expr $value]],"
    	}
    	incr i
	}
	close $file_id
}