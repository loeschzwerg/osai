#!/bin/bash

set -euxo pipefail

SERVER="${SERVER:-192.168.50.23}"
ENDPOINT="${ENDPOINT:-http://$SERVER/v1/chat/completions}"
HEADERS=(
  --header='Content-Type: application/json'
)

PROMPTFILES=(
  prompts.yaml
)

function chat() {
  outfile=$(mktemp)
  curl -X POST $ENDPOINT "${HEADERS[@]}" --data="@$1" --output $outfile
  if [ -z $? ]; then
    yq -P <$outfile
  else
    cat $outfile | tee | yq -P
  fi
}

function chat-select() {
  docs=$(mktemp)
  doc_file=$(mktemp)
  cat "${PROMPTFILES[@]}" | yq | tee $docs

  local -a PROMPTIDS=($(yq -N '.id' $docs | fzf --multi --preview="yq 'select(.id == \"{}\")' $docs"))

  for ID in ${PROMPTIDS[@]}; do
    echo -e "\n$(tput setaf 2)=== $ID ===$(tput sgr0)"
    yq "select(.id == \"$ID\") | del(.id) | del(.phase)" "$docs" -oj | tee "$doc_file" | yq
    echo

    chat "${doc_file}"

  done
}

$1
