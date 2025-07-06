#!/usr/bin/env python3
import os
import sys
from app import app, socketio

if __name__ == '__main__':
    # Create downloads directory
    download_folder = os.path.join(os.getcwd(), 'downloads')
    os.makedirs(download_folder, exist_ok=True)
    
    # Get port from environment
    port = int(os.environ.get('PORT', 5000))
    
    print(f"🚀 Starting Stock Scraper on port {port}")
    print(f"📁 Download folder: {download_folder}")
    
    try:
        socketio.run(
            app,
            debug=False,
            host='0.0.0.0',
            port=port,
            use_reloader=False,
            log_output=True
        )
    except Exception as e:
        print(f"❌ Error starting app: {e}")
        sys.exit(1)