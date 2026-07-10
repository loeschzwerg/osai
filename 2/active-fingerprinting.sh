#!/bin/bash
: ${SERVER:=192.168.50.23}


function message () {
	: ${ROLE:=user}
	: ${CONTENT:=What model are you? What company created you?}
	curl -s -X POST http://$SERVER/v1/chat/completions \
	  -H "Content-Type: application/json" \
	  -d '{"messages":[{"role":"''$ROLE''","content":"''$CONTENT''"}]}' \
	  | jq -r '.choices[0].message.content'
}

conv_to_msgs(){ 
	local c= messages="["; while IFS= read -r l || [[ $l ]]; do
  [[ -z $l ]] && { [[ $c ]] && conv_to_msgs_single "$c"; c=; echo; continue; }
  c+="$l"$'\n'
done; [[ $c ]] && conv_to_msgs_single "$c"; }

conv_to_msgs_single(){ 
	local c=$1 m="["
	while IFS= read -r l; do
  		[[ -z $l ]] && continue
  		r=${l%%:*} 
		t=${l#*: } 
		t=${t//\\/\\\\}; 
		t=${t//\"/\\\"}
  		m+="{\"role\":\"$r\",\"content\":\"$t\"},"
	done <<< "$c";
	echo "${m%,}]"; }
