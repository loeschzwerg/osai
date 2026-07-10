#!/bin/bash
set -u

. hosts.sh
SRV=${SRV:-${hosts[kb01]}}
SRV=${SRV:-${hosts[kb02]}}

PROMPTFILES=(
	prompts-rag.yaml
	prompts-siem.yaml
)

function grep_rag_info () {
	rg --ignore-case '^|chunk|vector|bm25|score|source|\.pdf|token|url|base|architecture|internal|secrets|retrieval'
}

function api_chat () {
	curl -s -X POST $SRV/api/chat \
	    -H "Content-Type: application/json" \
	    -d @${QUERY_FILE:-$1}
}

function api_chat-select () {
	docs=$(mktemp)
	doc_file=$(mktemp)
	cat "${PROMPTFILES[@]}" | yq > $docs

	local -a PROMPTIDS=($(yq -N '.id' $docs | fzf --multi --preview="yq 'select(.id == \"{}\")' $docs"))

	for ID in ${PROMPTIDS[@]} ; do
		echo -e "\n$(tput setaf 2)=== $ID ===$(tput sgr0)"
		yq "select(.id == \"$ID\")" "$docs" -oj | tee "$doc_file" | yq -P
		echo

		api_chat $doc_file | yq -P | grep_rag_info

	done
}

$1
