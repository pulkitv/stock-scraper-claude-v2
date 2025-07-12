#!/bin/bash
# Enhanced Screener API Shutdown Script

echo "🛑 Stopping Enhanced Screener API..."

if [ -f "api.pid" ]; then
    API_PID=$(cat api.pid)
    echo "🔍 Found API PID: $API_PID"
    
    if kill -0 $API_PID 2>/dev/null; then
        echo "🛑 Stopping API server..."
        kill $API_PID
        sleep 2
        
        # Force kill if still running
        if kill -0 $API_PID 2>/dev/null; then
            echo "⚠️ Force killing API server..."
            kill -9 $API_PID
        fi
    else
        echo "⚠️ API server not running"
    fi
    
    rm -f api.pid
    echo "✅ API server stopped"
else
    echo "⚠️ No PID file found"
fi

# Kill any remaining uvicorn processes
pkill -f "uvicorn.*screener_api" 2>/dev/null && echo "🧹 Cleaned up remaining processes"

echo "🎯 Shutdown complete!"
