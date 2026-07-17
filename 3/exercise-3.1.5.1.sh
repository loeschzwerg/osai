curl -s -X POST http://192.168..21:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What can you help me with?"}' | python3 -m json.tool

curl -s http://192.168.50.21:8001/health | python3 -m json.tool
