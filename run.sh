#!/bin/sh
cd "$(dirname "$0")/app" && python3 server.py "${1:-8000}"
