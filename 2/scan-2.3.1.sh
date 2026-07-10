#!/bin/bash

set -u

SRV=${SRV:-}

function grep_script () {
	curl -s $SRV | grep -iE "<script"
}

function js_chat_widget () {
	curl -s $SRV/js/chat-widget.js
}

function api_v2_assistant () {
	curl -s -X POST $SRV/api/v2/assistant \
	  -H "Content-Type: application/json" \
	  -d '{"message": "Hello"}'
}

function api_v1_billing () {
	curl -sI $SRV/v1/billing
}

function 401_vs_404 () {
	for endpoint in auth billing chat/completions models users; do
	  code=$(curl -s -o /dev/null -w "%{http_code}" \
	    $SRV/v1/$endpoint)
	  echo "/v1/$endpoint - HTTP $code"
	done
}

function v1_chat_completions () {
	curl -si $SRV/v1/chat/completions
}

function naive_fuzzer () {
	for endpoint in $(<apilist.txt) ; do
		code=$(curl -s -o /dev/null -w "%{http_code}" $SRV/$endpoint)
		echo "$code $SRV/$endpoint"
	done
}

function fuzzer () {
	wordlist=httparchive_apiroutes_2026_02_27.txt
	test -r $wordlist || wget https://wordlists-cdn.assetnote.io/data/automated/$wordlist
	if command -v kr ; then
		# using kiterunner
		kr scan --success-status-codes 200,401 -A=apiroutes-260227 $SRV
	elif command -v feroxbuster ; then
		# using feroxbuster
		feroxbuster -w $wordlist -u $SRV
	elif command -v ffuf ; then
		ffuf -w $wordlist -u $SRV/FUZZ
	else
		401_vs_404
	fi

}

case $1 in
	all)
		grep_script
		js_chat_widget
		api_v2_assistant
		api_v1_billing
		401_vs_404
		v1_chat_completions
		naive_fuzzer 
		fuzzer
		;;
	*)
		$1
		;;
esac
