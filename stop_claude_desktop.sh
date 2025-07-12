#!/bin/bash

echo "🛑 Stopping Claude Desktop Integration..."

# Kill processes from PID file
if [ -f "claude_desktop.pid" ]; then
    PIDS=$(cat claude_desktop.pid)
    for PID in $PIDS; do
        if kill -0 $PID 2>/dev/null; then
            echo "🛑 Stopping process $PID..."
            kill $PID
        fi
    done
    rm claude_desktop.pid
fi

# Kill any remaining processes
sudo lsof -ti:8001 | xargs kill -9 2>/dev/null || true
pkill -f "ngrok http 8001" 2>/dev/null || true
pkill -f "claude_desktop_api.py" 2>/dev/null || true

# Clean up files
rm -f ngrok_url.txt

echo "✅ Cleanup complete!"
