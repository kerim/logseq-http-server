#!/bin/bash
#
# Start the Logseq HTTP Server outside of Claude Code sandbox
# This allows the server to access Logseq database files
#

cd "$(dirname "$0")"

echo "Starting Logseq HTTP Server..."
echo "Server will run on http://localhost:8080"
echo "Press Ctrl+C to stop"
echo ""

python3 logseq_server.py --port 8080
