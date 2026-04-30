#!/bin/bash

#path to logs

dir="../EasyApt-main/backend/"

#log files that should exist
logs=("compliance_log.txt" "operations_log.txt" "backup_log.txt")

#used for exit status, will be 1 if there are errors
ERRSTAT=0

#checks for presence of specified logs, and checks to see if empty (improperly aggregating)
for log in "${logs[@]}"; do
	check="$dir$log"

#comparisons, first is existence, second is population
	if [[ ! -e "$check" ]]; then
		echo "$check IS MISSING"
		ERRSTAT=1
	fi

	if [[ ! -s "$check" ]]; then
		echo "$check IS EMPTY"
		ERRSTAT=1
	fi

done

#Checks if no errors are present, and outputs a message if there aren't any
if [[ "$ERRSTAT" -eq 0 ]]; then
	echo "All logs exist and are aggregating properly"
fi

exit "$ERRSTAT"
