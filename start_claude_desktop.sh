#!/bin/bash

echo "🚀 Starting Claude Desktop Integration..."

# Kill any existing processes on port 8001
echo "🧹 Cleaning up existing processes..."
sudo lsof -ti:8001 | xargs kill -9 2>/dev/null || true

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok not found. Installing..."
    brew install ngrok
fi

# Check if ngrok is authenticated
echo "🔐 Checking ngrok authentication..."
if ! ngrok config check &> /dev/null; then
    echo "❌ ngrok not authenticated!"
    echo "🔗 Please visit: https://dashboard.ngrok.com/signup"
    echo "📋 Then run: ngrok config add-authtoken YOUR_AUTHTOKEN"
    echo "💡 Get your authtoken from: https://dashboard.ngrok.com/get-started/your-authtoken"
    exit 1
fi

# Start API on port 8001
echo "🌐 Starting API server on port 8001..."
python claude_desktop_api.py &
API_PID=$!

# Wait for API to start
echo "⏳ Waiting for API to start..."
sleep 5

# Check if API is running
if curl -f http://localhost:8001/health > /dev/null 2>&1; then
    echo "✅ API is running"
else
    echo "❌ API failed to start"
    kill $API_PID 2>/dev/null || true
    exit 1
fi

# Start ngrok tunnel
echo "🔗 Starting ngrok tunnel..."
ngrok http 8001 > /dev/null 2>&1 &
NGROK_PID=$!

# Wait for ngrok to start
echo "⏳ Waiting for ngrok to start..."
sleep 5

# Get ngrok URL with better error handling
echo "📡 Getting ngrok URL..."
NGROK_URL=""
for i in {1..10}; do
    NGROK_URL=$(curl -s localhost:4040/api/tunnels 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'tunnels' in data and len(data['tunnels']) > 0:
        print(data['tunnels'][0]['public_url'])
    else:
        print('')
except:
    print('')
" 2>/dev/null)
    
    if [ ! -z "$NGROK_URL" ]; then
        break
    fi
    echo "⏳ Waiting for ngrok tunnel... (attempt $i)"
    sleep 2
done

if [ -z "$NGROK_URL" ]; then
    echo "❌ Failed to get ngrok URL"
    echo "🔍 Checking ngrok logs..."
    curl -s localhost:4040/api/tunnels 2>/dev/null || echo "No ngrok API response"
    kill $API_PID $NGROK_PID 2>/dev/null || true
    exit 1
fi

echo ""
echo "✅ Setup complete!"
echo "🔗 Your ngrok URL: $NGROK_URL"
echo "🎯 Use this URL in Claude Desktop"
echo ""
echo "📝 Example usage in Claude Desktop:"
echo "from claude_desktop_tool import get_company_analysis"
echo "result = get_company_analysis(['INFY'], '$NGROK_URL')"
echo ""
echo "🛑 To stop: ./stop_claude_desktop.sh"

# Save PIDs and URL for cleanup
echo "$API_PID $NGROK_PID" > claude_desktop.pid
echo "$NGROK_URL" > ngrok_url.txt