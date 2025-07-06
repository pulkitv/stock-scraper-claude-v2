#!/usr/bin/env python3
"""
Flask Web Application for Stock Scraper
Web-based UI for the Enhanced Screener.in scraper
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
import threading
import queue
import os
import json
from datetime import datetime
import time
import logging
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)

# Import our scraper
try:
    from screener_scraper import EnhancedScreenerScraper, CompanyData
    print("✅ Successfully imported EnhancedScreenerScraper")
except ImportError as e:
    print(f"❌ Import error: {e}")
    # Create fallback class
    class FallbackScreenerScraper:
        def __init__(self, delay=2):
            self.delay = delay
        def find_company_by_symbol(self, symbol):
            return None
        def extract_concall_data(self, url):
            return None
        def generate_filename(self, company, doc, index):
            return f"{company}_doc_{index}.pdf"
        def download_document(self, url, filename, download_dir):
            return False
    
    class FallbackCompanyData:
        def __init__(self, **kwargs):
            self.company_name = kwargs.get('company_name', '')
            self.symbol = kwargs.get('symbol', '')
            self.concalls = kwargs.get('concalls', [])
            self.annual_reports = kwargs.get('annual_reports', [])
    
    EnhancedScreenerScraper = FallbackScreenerScraper
    CompanyData = FallbackCompanyData

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables
is_scraping = False
scraping_thread = None
download_folder = os.path.join(os.getcwd(), 'downloads')

class ScrapingManager:
    def __init__(self):
        self.is_running = False
        self.progress_queue = queue.Queue()
        self.results = {}
        self.total_downloaded = 0
    
    def start_scraping(self, companies, doc_types, delay=2):
        """Start the scraping process"""
        self.is_running = True
        self.results = {}
        self.total_downloaded = 0
        
        # Create download directory
        os.makedirs(download_folder, exist_ok=True)
        
        # Start scraping in background thread
        thread = threading.Thread(target=self._scraping_worker, args=(companies, doc_types, delay))
        thread.daemon = True
        thread.start()
        
        return True
    
    def stop_scraping(self):
        """Stop the scraping process"""
        self.is_running = False
    
    def _scraping_worker(self, companies, doc_types, delay):
        """Background worker for scraping"""
        try:
            scraper = EnhancedScreenerScraper(delay=delay)
            
            socketio.emit('progress', {
                'type': 'status',
                'message': '🚀 ENHANCED SCRAPER v2.0 - Web Edition Started'
            })
            
            for i, company in enumerate(companies, 1):
                if not self.is_running:
                    break
                
                socketio.emit('progress', {
                    'type': 'status',
                    'message': f'Processing {company} ({i}/{len(companies)})'
                })
                
                try:
                    # Find company
                    company_url = scraper.find_company_by_symbol(company)
                    if not company_url:
                        socketio.emit('progress', {
                            'type': 'error',
                            'message': f'❌ Could not find company page for {company}'
                        })
                        continue
                    
                    socketio.emit('progress', {
                        'type': 'success',
                        'message': f'✅ Found: {company}'
                    })
                    
                    # Extract data
                    company_data = scraper.extract_concall_data(company_url)
                    if not company_data:
                        socketio.emit('progress', {
                            'type': 'error',
                            'message': f'❌ Could not extract data for {company}'
                        })
                        continue
                    
                    self.results[company] = company_data
                    
                    concalls = company_data.concalls or []
                    annual_reports = company_data.annual_reports or []
                    
                    socketio.emit('progress', {
                        'type': 'info',
                        'message': f'🏭 {company_data.company_name}: {len(concalls)} concalls, {len(annual_reports)} annual reports'
                    })
                    
                    # Download documents
                    download_dir = os.path.join(download_folder, company)
                    downloaded_count = 0
                    
                    # Download concalls
                    for j, concall in enumerate(concalls[:5]):  # Limit to 5
                        if not self.is_running:
                            break
                        
                        if doc_types.get('concalls', False):
                            filename = scraper.generate_filename(company, concall, j)
                            
                            socketio.emit('progress', {
                                'type': 'download',
                                'message': f'📥 Downloading: {filename}'
                            })
                            
                            if scraper.download_document(concall.url, filename, download_dir):
                                downloaded_count += 1
                                self.total_downloaded += 1
                                socketio.emit('progress', {
                                    'type': 'success',
                                    'message': f'✅ Downloaded: {filename}'
                                })
                            else:
                                socketio.emit('progress', {
                                    'type': 'error',
                                    'message': f'❌ Failed to download: {filename}'
                                })
                    
                    # Download annual reports
                    for j, report in enumerate(annual_reports[:3]):  # Limit to 3
                        if not self.is_running:
                            break
                        
                        if doc_types.get('annual_reports', False):
                            # Create temp document object
                            class TempDoc:
                                def __init__(self, **kwargs):
                                    for k, v in kwargs.items():
                                        setattr(self, k, v)
                            
                            temp_doc = TempDoc(
                                title=report.get('title', f'Annual Report {j+1}'),
                                url=report['url'],
                                doc_type='annual_report',
                                date=report.get('date', f'report-{j+1}')
                            )
                            
                            filename = scraper.generate_filename(company, temp_doc, j+100)
                            
                            socketio.emit('progress', {
                                'type': 'download',
                                'message': f'📥 Downloading: {filename}'
                            })
                            
                            if scraper.download_document(report['url'], filename, download_dir):
                                downloaded_count += 1
                                self.total_downloaded += 1
                                socketio.emit('progress', {
                                    'type': 'success',
                                    'message': f'✅ Downloaded: {filename}'
                                })
                            else:
                                socketio.emit('progress', {
                                    'type': 'error',
                                    'message': f'❌ Failed to download: {filename}'
                                })
                    
                    socketio.emit('progress', {
                        'type': 'info',
                        'message': f'📊 {company}: {downloaded_count} files downloaded'
                    })
                    
                except Exception as e:
                    socketio.emit('progress', {
                        'type': 'error',
                        'message': f'❌ Error processing {company}: {str(e)}'
                    })
            
            # Final summary
            socketio.emit('progress', {
                'type': 'complete',
                'message': f'🎉 Scraping complete! Total files downloaded: {self.total_downloaded}'
            })
            
        except Exception as e:
            socketio.emit('progress', {
                'type': 'error',
                'message': f'❌ Scraping error: {str(e)}'
            })
        finally:
            self.is_running = False

# Global scraping manager
scraping_manager = ScrapingManager()

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/start-scraping', methods=['POST'])
def start_scraping():
    """Start scraping process"""
    data = request.json or {}
    companies = [c.strip().upper() for c in data.get('companies', '').split(',') if c.strip()]
    doc_types = data.get('doc_types', {})
    delay = int(data.get('delay', 2))
    
    if not companies:
        return jsonify({'error': 'No companies specified'}), 400
    
    if scraping_manager.is_running:
        return jsonify({'error': 'Scraping already in progress'}), 400
    
    success = scraping_manager.start_scraping(companies, doc_types, delay)
    
    if success:
        return jsonify({'message': 'Scraping started successfully'})
    else:
        return jsonify({'error': 'Failed to start scraping'}), 500

@app.route('/api/stop-scraping', methods=['POST'])
def stop_scraping():
    """Stop scraping process"""
    scraping_manager.stop_scraping()
    return jsonify({'message': 'Scraping stopped'})

@app.route('/health')
def health_check():
    """Health check endpoint for Railway"""
    return jsonify({
        'status': 'healthy',
        'message': 'Stock Scraper is running',
        'download_folder': os.path.exists(download_folder)
    })

@app.route('/api/status')
def get_status():
    """Get current scraping status"""
    return jsonify({
        'is_running': scraping_manager.is_running,
        'total_downloaded': scraping_manager.total_downloaded,
        'download_folder': download_folder,
        'status': 'ready'
    })

@app.route('/downloads/<path:filename>')
def download_file(filename):
    """Serve downloaded files"""
    return send_from_directory(download_folder, filename)

@app.route('/api/files')
def list_files():
    """List all downloaded files"""
    files = []
    
    if os.path.exists(download_folder):
        for root, dirs, filenames in os.walk(download_folder):
            for filename in filenames:
                if filename.endswith(('.pdf', '.doc', '.docx', '.ppt', '.pptx')):
                    file_path = os.path.relpath(os.path.join(root, filename), download_folder)
                    company = os.path.basename(root) if root != download_folder else 'root'
                    file_size = os.path.getsize(os.path.join(root, filename))
                    modified_time = os.path.getmtime(os.path.join(root, filename))
                    
                    files.append({
                        'filename': filename,
                        'path': file_path,
                        'company': company,
                        'size': file_size,
                        'modified': datetime.fromtimestamp(modified_time).strftime('%Y-%m-%d %H:%M:%S'),
                        'download_url': f'/downloads/{file_path}'
                    })
    
    return jsonify({'files': files})

@app.route('/api/download-path')
def get_download_path():
    """Get the current download folder path"""
    return jsonify({
        'download_folder': download_folder,
        'absolute_path': os.path.abspath(download_folder),
        'exists': os.path.exists(download_folder)
    })

@app.route('/api/files/clear', methods=['POST'])
def clear_files():
    """Clear all downloaded files"""
    try:
        import shutil
        if os.path.exists(download_folder):
            shutil.rmtree(download_folder)
            os.makedirs(download_folder, exist_ok=True)
        return jsonify({'message': 'All files cleared successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-download', methods=['POST'])
def test_download():
    """Test downloading a specific URL"""
    data = request.json
    test_url = data.get('url')
    
    if not test_url:
        return jsonify({'error': 'URL required'}), 400
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(test_url, headers=headers, timeout=30)
        
        return jsonify({
            'status_code': response.status_code,
            'content_type': response.headers.get('Content-Type'),
            'content_length': response.headers.get('Content-Length'),
            'url': response.url,
            'is_pdf': 'pdf' in response.headers.get('Content-Type', '').lower(),
            'preview': response.text[:200] if response.text else 'No text content'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    emit('connected', {'data': 'Connected to Stock Scraper'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

def initialize_app():
    """Initialize app"""
    logging.info("Initializing Stock Scraper...")
    os.makedirs(download_folder, exist_ok=True)
    logging.info(f"Download folder created: {download_folder}")

# Initialize app immediately
initialize_app()

@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    logging.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found'}), 404

if __name__ == '__main__':
    # This block only runs when app.py is executed directly
    # NOT when imported by gunicorn
    port = int(os.environ.get('PORT', 5000))
    os.makedirs(download_folder, exist_ok=True)
    
    print(f"🚀 Starting Stock Scraper locally on port {port}")
    socketio.run(
        app,
        debug=True,
        host='0.0.0.0',
        port=port,
        allow_unsafe_werkzeug=True
    )