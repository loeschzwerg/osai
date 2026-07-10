#!/usr/bin/bash
IP=192.186.147.31 # 22, 80, 8000
# IP=192.186.147.32 # 22, 80, 3000, 9000 
PORT=80 

curl -s http://$IP/ | grep -iE "<script" # js/chat-widget.js

curl -s http://$IP/js/chat-widget.js # assistantEndpoint

curl -s -X POST http://$IP/api/v2/assistant \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}' | jq

curl -sI http://$IP:$PORT/v1/billing

for endpoint in auth billing chat/completions models users; do
  code=$(curl -s -o /dev/null -w "%{http_code}" \
    http://$IP:$PORT/v1/$endpoint)
  echo "/v1/$endpoint - HTTP $code"
done

ferox_args=(
	--url http://$IP
	--collect-words # --smart
	--methods POST GET
	--insecure
	--wordlist /usr/share/seclists/Discovery/Web-Content/raft-small-directories.txt
	--threads 10
	--unique
	# --output feroxbuster.scan
	--headers 'Accept: application/json'
	# --status-codes 200 401 403 500 503
)


feroxbuster "${ferox_args[@]}" --wordlist <<EOF
	/v1/auth
	/v1/billing
	/v1/chat/completions
	/v1/models
	/v1/users
EOF
