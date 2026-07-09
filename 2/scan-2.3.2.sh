#!/bin/bash

HOSTNAME="${HOSTNAME:-192.168.50.23}"
ENDPOINT="${ENDPOINT:-http://$HOSTNAME/v1/chat/completions}"
HEADERS=(
  --header='Content-Type: application/json'
)

PROMPTFILES=(
  prompts.yaml
)

function chat () {
  outfile=$(mktemp)
  curl -X POST $HOSTNAME "${HEADERS[@]}" --data="@$1" --output $outfile
  if [ -z $? ] ; then
    yq -P < $outfile
  else
    cat $outfile
  fi
}


function chat-select () {
  docs=$(mktemp)
  doc_file=$(mktemp)
  yq ${PROMPTFILES[@]} > $docs
  
  local -a PROMPTIDS=($(yq -N '.id' $docs | fzf --multi --preview="yq 'select(.id == \"{}\")' $docs"))

  for ID in ${PROMPTIDS[@]} ; do
    echo "\n$(tput setaf 2)=== $ID ===$(tput sgr0)"
    yq "select(.id == \"$ID\") | del(.id) | del(.phase)" "$docs" | tee "$doc_file" | yq
    echo 
    
    chat "${doc_file}"

  done
}
