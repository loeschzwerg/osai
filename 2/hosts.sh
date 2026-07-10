#!/bin/bash

x=${x:-$1}
declare -A -x hosts
hosts[chat01]=192.168.$x.21
hosts[chat02]=192.168.$x.23
hosts[chat03]=192.168.$x.24
hosts[chat03]=192.168.$x.26
hosts[kb01]=192.168.$x.28
hosts[kb02]=192.168.$x.34
hosts[siem01]=192.168.$x.30 # offsec / lab123
hosts[webapp01]=192.168.$x.31
hosts[webapp02]=192.168.$x.32

