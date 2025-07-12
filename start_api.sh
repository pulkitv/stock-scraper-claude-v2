#!/bin/bash
# Enhanced Screener API Startup Script

echo "🚀 Starting Enhanced Screener API for Claude..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Start the API server
echo "🌐 Starting API server..."
python screener_api.py &

# Store PID for shutdown
API_PID=$!
echo $API_PID > api.pid

echo "✅ API server started with PID: $API_PID"
echo "🔗 API available at: http://localhost:8000"
echo "📊 API docs at: http://localhost:8000/docs"

# Wait for server to start
sleep 3

# Test API health
echo "🏥 Testing API health..."
curl -f http://localhost:8000/health || echo "⚠️ API health check failed"

echo "🎯 Ready for Claude integration!"
