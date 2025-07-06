"""
WSGI entry point for production deployment
"""
import os
from app import app, socketio

# Create downloads directory
download_folder = os.path.join(os.getcwd(), 'downloads')
os.makedirs(download_folder, exist_ok=True)

# This is what gunicorn will use
application = app

if __name__ == "__main__":
    # Fallback for direct execution
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)