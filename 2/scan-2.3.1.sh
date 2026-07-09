#!/bin/bash

set -euxo pippefail

SERVERS=(
	192.168.166.31
	http://192.168.166.32:9000
)

for SRV in "${SERVERS[@]}" ; do
	# using kiterunner
	kr scan --success-status-codes 200,401 -A=apiroutes-260227 $SRV	
	# using feroxbuster
	wget https://wordlists-cdn.assetnote.io/data/automated/httparchive_apiroutes_2026_02_27.txt
	feroxbuster -w httparchive_apiroutes_2026_02_27.txt -u $SRV
done
