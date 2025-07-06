#!/usr/bin/env python3
import os
from app import app, socketio

if __name__ == "__main__":
    # Get port from environment
    port = int(os.environ.get('PORT', 5000))
    
    # Create downloads directory
    download_folder = os.path.join(os.getcwd(), 'downloads')
    os.makedirs(download_folder, exist_ok=True)
    
    print(f"🚀 Starting Stock Scraper on port {port}")
    print(f"📁 Download folder: {download_folder}")
    
    # Use eventlet for production
    socketio.run(
        app,
        debug=False,
        host='0.0.0.0',
        port=port,
        use_reloader=False,
        allow_unsafe_werkzeug=True  # This fixes the Werkzeug error
    )

# For gunicorn
application = app