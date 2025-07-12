#!/bin/bash

echo "🚀 Setting up Ultimate Claude Desktop Integration..."
echo "No manual code sharing required!"

# Kill any existing processes
echo "🧹 Cleaning up..."
sudo lsof -ti:8001 | xargs kill -9 2>/dev/null || true

# Start the enhanced API
echo "🌐 Starting Claude-integrated API..."
python claude_integrated_api.py &
API_PID=$!

# Wait for API to start
sleep 5

# Check if API is running
if curl -f http://localhost:8001/claude-ready > /dev/null 2>&1; then
    echo "✅ API is running and Claude-ready"
else
    echo "❌ API failed to start"
    kill $API_PID 2>/dev/null || true
    exit 1
fi

# Start ngrok
echo "🔗 Starting ngrok tunnel..."
ngrok http 8001 --log=stdout > ngrok.log 2>&1 &
NGROK_PID=$!

# Wait for ngrok
sleep 5

# Get ngrok URL
NGROK_URL=$(curl -s localhost:4040/api/tunnels | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data['tunnels'][0]['public_url'])
except:
    print('')
")

if [ -z "$NGROK_URL" ]; then
    echo "❌ Failed to get ngrok URL"
    kill $API_PID $NGROK_PID 2>/dev/null || true
    exit 1
fi

# Test the Claude integration
echo "🧪 Testing Claude integration..."
curl -s "$NGROK_URL/claude-ready" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('claude_ready'):
        print('✅ Claude integration test passed')
    else:
        print('❌ Claude integration test failed')
except:
    print('❌ Claude integration test failed')
"

echo ""
echo "🎉 Ultimate Claude Desktop Integration Complete!"
echo "=" * 60
echo "🔗 Your API URL: $NGROK_URL"
echo "📋 Claude can now call these endpoints directly:"
echo "   • $NGROK_URL/analyze/INFY"
echo "   • $NGROK_URL/compare?companies=INFY&companies=TCS"
echo "   • $NGROK_URL/sector/it"
echo "   • $NGROK_URL/claude-instructions"
echo ""
echo "💬 Tell Claude:"
echo "   'I have a stock analysis API at $NGROK_URL'"
echo "   'Please analyze Infosys using the /analyze/INFY endpoint'"
echo ""
echo "🛑 To stop: kill $API_PID $NGROK_PID"

# Save for reference
echo "$NGROK_URL" > ngrok_url.txt
echo "$API_PID $NGROK_PID" > claude_integration.pid

echo "🔗 API URL saved to ngrok_url.txt"
echo "🎯 Your stock scraper is now Claude Desktop ready!"