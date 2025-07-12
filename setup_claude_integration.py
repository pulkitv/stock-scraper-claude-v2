#!/usr/bin/env python3
"""
Setup script for Claude integration with Enhanced Screener
"""

import os
import subprocess
import sys
import json
from pathlib import Path

def install_dependencies():
    """Install required dependencies"""
    print("🔧 Installing dependencies...")
    
    dependencies = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "python-multipart",
        "requests",
        "asyncio",
    ]
    
    for dep in dependencies:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"✅ Installed {dep}")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {dep}")
            return False
    
    return True

def create_config_file():
    """Create configuration file"""
    config = {
        "api": {
            "host": "0.0.0.0",
            "port": 8000,
            "debug": False
        },
        "scraper": {
            "default_delay": 2,
            "max_concalls": 20,
            "max_annual_reports": 5,
            "download_timeout": 30
        },
        "claude": {
            "tools_enabled": True,
            "max_companies_per_request": 10,
            "analysis_cache_ttl": 3600
        }
    }
    
    config_path = Path("claude_config.json")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Created config file: {config_path}")
    return config_path

def create_startup_script():
    """Create startup script"""
    startup_script = '''#!/bin/bash
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
'''
    
    script_path = Path("start_api.sh")
    with open(script_path, 'w') as f:
        f.write(startup_script)
    
    # Make executable
    os.chmod(script_path, 0o755)
    print(f"✅ Created startup script: {script_path}")
    return script_path

def create_shutdown_script():
    """Create shutdown script"""
    shutdown_script = '''#!/bin/bash
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
'''
    
    script_path = Path("stop_api.sh")
    with open(script_path, 'w') as f:
        f.write(shutdown_script)
    
    # Make executable
    os.chmod(script_path, 0o755)
    print(f"✅ Created shutdown script: {script_path}")
    return script_path

def create_claude_instructions():
    """Create instructions for Claude integration"""
    instructions = """
# Claude Integration Instructions

## Setup Complete! 🎉

Your Enhanced Screener is now ready for Claude integration.

## Quick Start:

1. **Start the API server:**
   ```bash
   ./start_api.sh
   ```

2. **Test the API:**
   ```bash
   curl http://localhost:8000/health
   ```

3. **Use with Claude:**
   Claude can now call these functions:
   - `get_company_reports_tool(symbols)` - Fetch company reports
   - `search_company_tool(query)` - Search for companies
   - `list_company_files_tool(symbol)` - List downloaded files
   - `analyze_company_trends_tool(symbols, focus)` - Analyze trends

## Example Claude Usage:

**Claude:** "Can you analyze the latest earnings reports for Apple and Microsoft?"

**You:** Use the tool: `get_company_reports_tool(["AAPL", "MSFT"])`

**Claude:** Will fetch the data and provide analysis based on the reports.

## API Endpoints:

- **Health Check:** http://localhost:8000/health
- **API Docs:** http://localhost:8000/docs
- **Search Company:** http://localhost:8000/search-companies/{query}
- **Fetch Reports:** POST http://localhost:8000/fetch-company-data

## Tool Functions for Claude:

```python
# In your Claude conversation, you can use:
from claude_screener_tool import get_company_reports_tool

# Fetch reports for companies
result = get_company_reports_tool(["INFY", "TCS"])

# Search for a company
result = search_company_tool("Infosys")

# List downloaded files
result = list_company_files_tool("INFY")
```

## Configuration:

Edit `claude_config.json` to customize:
- API settings (host, port)
- Scraper settings (delays, limits)
- Claude integration settings

## Troubleshooting:

1. **API not starting:** Check if port 8000 is available
2. **Permission errors:** Run `chmod +x *.sh` to make scripts executable
3. **Module errors:** Ensure all dependencies are installed in your virtual environment

## Next Steps:

1. Test the API with a simple company search
2. Try fetching reports for a known company (like INFY)
3. Integrate with your Claude workflow
4. Customize the analysis functions for your needs

## Support:

- API logs are available in the console
- Check `api.pid` file for server status
- Use `./stop_api.sh` to cleanly shutdown

Happy analyzing! 📊
"""
    
    readme_path = Path("CLAUDE_INTEGRATION.md")
    with open(readme_path, 'w') as f:
        f.write(instructions)
    
    print(f"✅ Created instructions: {readme_path}")
    return readme_path

def test_installation():
    """Test the installation"""
    print("\n🧪 Testing installation...")
    
    try:
        # Test imports
        import fastapi
        import uvicorn
        import pydantic
        print("✅ All dependencies imported successfully")
        
        # Test screener import
        from screener_scraper import EnhancedScreenerScraper
        print("✅ Enhanced Screener imported successfully")
        
        # Test tool import
        from claude_screener_tool import ScreenerTool
        print("✅ Claude tools imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up Claude Integration for Enhanced Screener")
    print("=" * 60)
    
    # Step 1: Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        return False
    
    # Step 2: Create configuration
    config_path = create_config_file()
    
    # Step 3: Create scripts
    start_script = create_startup_script()
    stop_script = create_shutdown_script()
    
    # Step 4: Create instructions
    instructions = create_claude_instructions()
    
    # Step 5: Test installation
    if not test_installation():
        print("❌ Installation test failed")
        return False
    
    print("\n" + "=" * 60)
    print("✅ Claude Integration Setup Complete!")
    print("=" * 60)
    print(f"📁 Config file: {config_path}")
    print(f"🚀 Start script: {start_script}")
    print(f"🛑 Stop script: {stop_script}")
    print(f"📖 Instructions: {instructions}")
    print("\n🎯 Next steps:")
    print("1. Run ./start_api.sh to start the API")
    print("2. Test with: curl http://localhost:8000/health")
    print("3. Read CLAUDE_INTEGRATION.md for usage instructions")
    print("4. Start using with Claude!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)