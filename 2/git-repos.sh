#!/bin/bash

# IP=192.168.169.22
IP=192.168.147.22



BRANCH="main"
SUFFIX="tar.gz"

function download() {
	ARCHIVE="-/archive/${BRANCH}/${REPO}-${BRANCH}"
	wget "http://${IP}/${GROUP}/${REPO}/${ARCHIVE}.$SUFFIX"
}

curl -I http://$IP/explore

if [[ $? == 0 ]] ; then
	echo "Hurra!"
fi

GROUP=aurora  REPO=support-assistant  download
GROUP=phoenix REPO=code-reviewer      download
GROUP=nebula  REPO=data-analyst       download
GROUP=titan   REPO=document-processor download

git clone http://$IP/aurora/support-assistant.git
git clone http://$IP/phoenix/code-reviewer.git
git clone http://$IP/nebula/data-analyst.git
git clone http://$IP/titan/document-processor.git
