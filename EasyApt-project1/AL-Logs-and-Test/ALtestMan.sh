#!/bin/bash
#checking for args, if none output usage info, else run script
if [ $# -eq 0 ]; then
	echo "A.Lambrecht Test Manager usage: Run script with filenames for tests"
	echo "in current directory as arguments to run and track results."
	echo "All files provided must be executable in order to function, failure"
	echo "to do so may cause this script to function improperly."
	echo "Use as -m arg by itself to run the makefile tests"
	echo "Running this script with no arguments will produce this message again."

#Runs all provided tests and checks for successful operation
else

	#clears last test results, please ensure you back them up before re-running if necessary
	output_file="testManResults.txt"
	> "$output_file"

	#checks for makefile flag, runs and makes output file if so
	if [[ $# -eq 1 && "$1" == "-m" ]]; then
		(cd ../EasyApt-main/ && make test) >> "$output_file"

		exit 0;
	fi
	#Creates a temporary output directory
	temp_dir=$(mktemp -d)

	#tracks process ids
	pids=()

	#loops through args and processes scripts
	for test in "$@"; do
		(
			#creates temp file for logs
			temp_out="$temp_dir/$(basename "$test").out"

			#formatting stuff for the output file
			echo "______________________" >>  "$output_file"
			echo "Running: $test" >> "$output_file"
			echo "______________________" >> "$temp_out"

			#simple executability check, may not catch all cases, will run script if this passes
			if [ -x "$test" ]; then
				"./$test" >> "$temp_out" 2>&1
				exit_stat=$?
				echo "Exit Status: $exit_stat" >> "$temp_out"
			#Catches nonexetutables
			else
				echo "ERR: $test is not executable." >> "$output_file"
			fi

			echo "" >> "$output_file"
		) &

		pids+=($!)
	done

	#Waiting for background tests to finish up
	for pid in "${pids[@]}"; do
		wait "$pid"
	done

	#combine outputs
	cat "$temp_dir"/*.out >> "$output_file"

	#Cleanup of temp dirs
	rm -r "$temp_dir"

	echo "Test outputs written to $output_file"
fi

exit 0
