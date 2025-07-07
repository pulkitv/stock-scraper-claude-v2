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
        def get_actual_pdf_link(self, url):
            return None
    
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
        self.is_running = False
    
    def _scraping_worker(self, companies, doc_types, delay):
        """Background worker for scraping"""
        try:
            scraper = EnhancedScreenerScraper(delay=delay)
            
            # Send initial progress with stats
            socketio.emit('progress', {
                'type': 'status',
                'message': '🚀 ENHANCED SCRAPER v2.0 - Web Edition Started',
                'stats': {
                    'total_downloaded': self.total_downloaded,
                    'companies_processed': 0,
                    'total_companies': len(companies)
                }
            })
            
            companies_processed = 0
            
            for i, company in enumerate(companies, 1):
                if not self.is_running:
                    break
                
                socketio.emit('progress', {
                    'type': 'status',
                    'message': f'Processing {company} ({i}/{len(companies)})',
                    'stats': {
                        'total_downloaded': self.total_downloaded,
                        'companies_processed': companies_processed,
                        'total_companies': len(companies)
                    }
                })
                
                try:
                    # Find company
                    company_url = scraper.find_company_by_symbol(company)
                    if not company_url:
                        socketio.emit('progress', {
                            'type': 'error',
                            'message': f'❌ Could not find company page for {company}',
                            'stats': {
                                'total_downloaded': self.total_downloaded,
                                'companies_processed': companies_processed,
                                'total_companies': len(companies)
                            }
                        })
                        continue
                    
                    socketio.emit('progress', {
                        'type': 'success',
                        'message': f'✅ Found: {company}',
                        'stats': {
                            'total_downloaded': self.total_downloaded,
                            'companies_processed': companies_processed,
                            'total_companies': len(companies)
                        }
                    })
                    
                    # Extract data
                    company_data = scraper.extract_concall_data(company_url)
                    if not company_data:
                        socketio.emit('progress', {
                            'type': 'error',
                            'message': f'❌ Could not extract data for {company}',
                            'stats': {
                                'total_downloaded': self.total_downloaded,
                                'companies_processed': companies_processed,
                                'total_companies': len(companies)
                            }
                        })
                        continue
                    
                    self.results[company] = company_data
                    
                    # Get ALL concalls (not just first 5)
                    all_concalls = company_data.concalls or []
                    annual_reports = company_data.annual_reports or []
                    
                    socketio.emit('progress', {
                        'type': 'info',
                        'message': f'🏭 {company_data.company_name}: {len(all_concalls)} total concalls, {len(annual_reports)} annual reports',
                        'stats': {
                            'total_downloaded': self.total_downloaded,
                            'companies_processed': companies_processed,
                            'total_companies': len(companies)
                        }
                    })
                    
                    # Download documents
                    download_dir = os.path.join(download_folder, company)
                    downloaded_count = 0
                    
                    # Download concalls with priority fallback system
                    if doc_types.get('concalls', False):
                        # Group ALL concalls by quarter/date
                        concall_groups = {}
                        for concall in all_concalls:  # Process ALL concalls
                            # Use date as grouping key
                            date_key = concall.date or 'unknown'
                            if date_key not in concall_groups:
                                concall_groups[date_key] = []
                            concall_groups[date_key].append(concall)
                        
                        socketio.emit('progress', {
                            'type': 'info',
                            'message': f'📊 Found {len(concall_groups)} unique quarter groups: {list(concall_groups.keys())}',
                            'stats': {
                                'total_downloaded': self.total_downloaded,
                                'companies_processed': companies_processed,
                                'total_companies': len(companies)
                            }
                        })
                        
                        # Sort quarters by date (most recent first) and take top 5
                        sorted_quarters = []
                        for quarter_date, quarter_concalls in concall_groups.items():
                            # Use the most recent concall in this quarter to represent the quarter
                            quarter_concalls.sort(key=lambda x: x.parsed_date or datetime.min, reverse=True)
                            latest_concall = quarter_concalls[0]
                            sorted_quarters.append((quarter_date, quarter_concalls, latest_concall.parsed_date or datetime.min))
                        
                        # Sort by date (most recent first) and take top 5
                        sorted_quarters.sort(key=lambda x: x[2], reverse=True)
                        top_5_quarters = sorted_quarters[:5]  # Take TOP 5 quarters
                        
                        socketio.emit('progress', {
                            'type': 'info',
                            'message': f'📅 Selected TOP 5 quarters: {[q[0] for q in top_5_quarters]}',
                            'stats': {
                                'total_downloaded': self.total_downloaded,
                                'companies_processed': companies_processed,
                                'total_companies': len(companies)
                            }
                        })
                        
                        # Process each of the top 5 quarters with fallback priority
                        for quarter_index, (quarter_date, quarter_concalls, quarter_parsed_date) in enumerate(top_5_quarters, 1):
                            if not self.is_running:
                                break
                            
                            socketio.emit('progress', {
                                'type': 'info',
                                'message': f'📅 Processing Quarter {quarter_index}/5: {quarter_date} ({len(quarter_concalls)} documents available)',
                                'stats': {
                                    'total_downloaded': self.total_downloaded,
                                    'companies_processed': companies_processed,
                                    'total_companies': len(companies)
                                }
                            })
                            
                            # Sort by priority: transcript > notes > ppt > others
                            def get_priority(concall):
                                doc_type = concall.doc_type.lower()
                                if 'transcript' in doc_type:
                                    return 1
                                elif 'notes' in doc_type:
                                    return 2
                                elif 'ppt' in doc_type or 'presentation' in doc_type:
                                    return 3
                                else:
                                    return 4
                            
                            quarter_concalls.sort(key=get_priority)
                            
                            # Show available documents for this quarter
                            available_docs = [f"{c.doc_type}({get_priority(c)})" for c in quarter_concalls]
                            socketio.emit('progress', {
                                'type': 'info',
                                'message': f'📋 {quarter_date} available: {", ".join(available_docs)}',
                                'stats': {
                                    'total_downloaded': self.total_downloaded,
                                    'companies_processed': companies_processed,
                                    'total_companies': len(companies)
                                }
                            })
                            
                            # Try each document type in priority order
                            quarter_downloaded = False
                            for attempt, concall in enumerate(quarter_concalls, 1):
                                if not self.is_running or quarter_downloaded:
                                    break
                                
                                doc_type = concall.doc_type.lower()
                                priority_name = ""
                                
                                if 'transcript' in doc_type:
                                    priority_name = "Transcript (Priority 1)"
                                elif 'notes' in doc_type:
                                    priority_name = "Notes (Priority 2)"
                                elif 'ppt' in doc_type or 'presentation' in doc_type:
                                    priority_name = "PPT (Priority 3)"
                                else:
                                    priority_name = f"Other ({doc_type})"
                                
                                filename = scraper.generate_filename(company, concall, downloaded_count)
                                
                                socketio.emit('progress', {
                                    'type': 'download',
                                    'message': f'📥 Quarter {quarter_index}: Trying {priority_name} - {filename}',
                                    'stats': {
                                        'total_downloaded': self.total_downloaded,
                                        'companies_processed': companies_processed,
                                        'total_companies': len(companies)
                                    }
                                })
                                
                                try:
                                    # Attempt download
                                    download_success = scraper.download_document(concall.url, filename, download_dir)
                                    
                                    if download_success:
                                        downloaded_count += 1
                                        self.total_downloaded += 1  # Increment total counter
                                        quarter_downloaded = True
                                        
                                        socketio.emit('progress', {
                                            'type': 'success',
                                            'message': f'✅ Quarter {quarter_index}: Downloaded {priority_name} - {filename}',
                                            'stats': {
                                                'total_downloaded': self.total_downloaded,
                                                'companies_processed': companies_processed,
                                                'total_companies': len(companies)
                                            }
                                        })
                                        
                                        # Send separate stats update
                                        socketio.emit('stats_update', {
                                            'total_downloaded': self.total_downloaded,
                                            'companies_processed': companies_processed,
                                            'total_companies': len(companies),
                                            'success_rate': round((self.total_downloaded / max(1, (quarter_index * i))) * 100, 1)
                                        })
                                        
                                        break  # Successfully downloaded, move to next quarter
                                    else:
                                        socketio.emit('progress', {
                                            'type': 'warning',
                                            'message': f'⚠️ Quarter {quarter_index}: Failed {priority_name} - {filename}',
                                            'stats': {
                                                'total_downloaded': self.total_downloaded,
                                                'companies_processed': companies_processed,
                                                'total_companies': len(companies)
                                            }
                                        })
                                        
                                        # If this was PPT (priority 3) and it failed, give up on this quarter
                                        if 'ppt' in doc_type or 'presentation' in doc_type:
                                            socketio.emit('progress', {
                                                'type': 'error',
                                                'message': f'❌ Quarter {quarter_index}: All priorities failed for {quarter_date} - giving up',
                                                'stats': {
                                                    'total_downloaded': self.total_downloaded,
                                                    'companies_processed': companies_processed,
                                                    'total_companies': len(companies)
                                                }
                                            })
                                            break
                                            
                                except Exception as download_error:
                                    socketio.emit('progress', {
                                        'type': 'error',
                                        'message': f'❌ Quarter {quarter_index}: Download error for {priority_name}: {str(download_error)}',
                                        'stats': {
                                            'total_downloaded': self.total_downloaded,
                                            'companies_processed': companies_processed,
                                            'total_companies': len(companies)
                                        }
                                    })
                                    
                                    # If this was PPT (priority 3) and it failed, give up on this quarter
                                    if 'ppt' in doc_type or 'presentation' in doc_type:
                                        socketio.emit('progress', {
                                            'type': 'error',
                                            'message': f'❌ Quarter {quarter_index}: All priorities failed for {quarter_date} - giving up',
                                            'stats': {
                                                'total_downloaded': self.total_downloaded,
                                                'companies_processed': companies_processed,
                                                'total_companies': len(companies)
                                            }
                                        })
                                        break
                            
                            # If nothing was downloaded for this quarter
                            if not quarter_downloaded:
                                socketio.emit('progress', {
                                    'type': 'error',
                                    'message': f'❌ Quarter {quarter_index}: No documents downloaded for {quarter_date}',
                                    'stats': {
                                        'total_downloaded': self.total_downloaded,
                                        'companies_processed': companies_processed,
                                        'total_companies': len(companies)
                                    }
                                })
                        
                        # Summary of concall downloads
                        socketio.emit('progress', {
                            'type': 'info',
                            'message': f'📊 Concall Summary: Processed {len(top_5_quarters)} quarters, downloaded {downloaded_count} concall documents',
                            'stats': {
                                'total_downloaded': self.total_downloaded,
                                'companies_processed': companies_processed,
                                'total_companies': len(companies)
                            }
                        })
                    
                    # Download annual reports
                    if doc_types.get('annual_reports', False):
                        socketio.emit('progress', {
                            'type': 'info',
                            'message': f'📋 Starting annual reports download ({len(annual_reports[:3])} reports)',
                            'stats': {
                                'total_downloaded': self.total_downloaded,
                                'companies_processed': companies_processed,
                                'total_companies': len(companies)
                            }
                        })
                        
                        for j, report in enumerate(annual_reports[:3]):  # Limit to 3
                            if not self.is_running:
                                break
                            
                            try:
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
                                    'message': f'📥 Annual Report {j+1}/3: {filename}',
                                    'stats': {
                                        'total_downloaded': self.total_downloaded,
                                        'companies_processed': companies_processed,
                                        'total_companies': len(companies)
                                    }
                                })
                                
                                # Attempt download
                                download_success = scraper.download_document(report['url'], filename, download_dir)
                                
                                if download_success:
                                    downloaded_count += 1
                                    self.total_downloaded += 1  # Increment total counter
                                    
                                    socketio.emit('progress', {
                                        'type': 'success',
                                        'message': f'✅ Annual Report {j+1}/3: Downloaded {filename}',
                                        'stats': {
                                            'total_downloaded': self.total_downloaded,
                                            'companies_processed': companies_processed,
                                            'total_companies': len(companies)
                                        }
                                    })
                                    
                                    # Send separate stats update
                                    socketio.emit('stats_update', {
                                        'total_downloaded': self.total_downloaded,
                                        'companies_processed': companies_processed,
                                        'total_companies': len(companies),
                                        'success_rate': round((self.total_downloaded / max(1, (j + 1) * i)) * 100, 1)
                                    })
                                    
                                else:
                                    socketio.emit('progress', {
                                        'type': 'error',
                                        'message': f'❌ Annual Report {j+1}/3: Failed to download {filename}',
                                        'stats': {
                                            'total_downloaded': self.total_downloaded,
                                            'companies_processed': companies_processed,
                                            'total_companies': len(companies)
                                        }
                                    })
                                    
                            except Exception as annual_error:
                                socketio.emit('progress', {
                                    'type': 'error',
                                    'message': f'❌ Annual Report {j+1}/3: Download error: {str(annual_error)}',
                                    'stats': {
                                        'total_downloaded': self.total_downloaded,
                                        'companies_processed': companies_processed,
                                        'total_companies': len(companies)
                                    }
                                })
                    
                    companies_processed += 1
                    
                    socketio.emit('progress', {
                        'type': 'info',
                        'message': f'📊 {company} TOTAL: {downloaded_count} files downloaded',
                        'stats': {
                            'total_downloaded': self.total_downloaded,
                            'companies_processed': companies_processed,
                            'total_companies': len(companies)
                        }
                    })
                    
                except Exception as company_error:
                    socketio.emit('progress', {
                        'type': 'error',
                        'message': f'❌ Error processing {company}: {str(company_error)}',
                        'stats': {
                            'total_downloaded': self.total_downloaded,
                            'companies_processed': companies_processed,
                            'total_companies': len(companies)
                        }
                    })
                    companies_processed += 1
            
            # Final summary
            final_success_rate = round((self.total_downloaded / max(1, companies_processed * 8)) * 100, 1) if companies_processed > 0 else 0
            
            socketio.emit('progress', {
                'type': 'complete',
                'message': f'🎉 Scraping complete! Total files downloaded: {self.total_downloaded}',
                'stats': {
                    'total_downloaded': self.total_downloaded,
                    'companies_processed': companies_processed,
                    'total_companies': len(companies),
                    'success_rate': final_success_rate
                }
            })
            
            # Send final stats update
            socketio.emit('stats_update', {
                'total_downloaded': self.total_downloaded,
                'companies_processed': companies_processed,
                'total_companies': len(companies),
                'success_rate': final_success_rate,
                'is_complete': True
            })
            
        except Exception as e:
            socketio.emit('progress', {
                'type': 'error',
                'message': f'❌ Scraping error: {str(e)}',
                'stats': {
                    'total_downloaded': self.total_downloaded,
                    'companies_processed': 0,
                    'total_companies': len(companies) if companies else 0
                }
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
    data = request.json or {}
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

@app.route('/api/debug-annual-reports/<symbol>')
def debug_annual_reports(symbol):
    """Debug annual reports for a specific company"""
    try:
        scraper = EnhancedScreenerScraper(delay=1)
        
        # Find company
        company_url = scraper.find_company_by_symbol(symbol.upper())
        if not company_url:
            return jsonify({'error': f'Could not find company page for {symbol}'}), 404
        
        # Extract data
        company_data = scraper.extract_concall_data(company_url)
        if not company_data:
            return jsonify({'error': f'Could not extract data for {symbol}'}), 404
        
        # Test each annual report URL
        debug_results = []
        for report in company_data.annual_reports:
            try:
                url = report['url']
                
                # Test the URL
                response = requests.get(url, timeout=10)
                
                # Try to find actual PDF link if it's HTML
                actual_pdf_url = None
                if 'text/html' in response.headers.get('Content-Type', '').lower():
                    actual_pdf_url = scraper.get_actual_pdf_link(url)
                
                debug_results.append({
                    'title': report['title'],
                    'original_url': url,
                    'status_code': response.status_code,
                    'content_type': response.headers.get('Content-Type', ''),
                    'content_length': response.headers.get('Content-Length', ''),
                    'is_html': 'text/html' in response.headers.get('Content-Type', '').lower(),
                    'actual_pdf_url': actual_pdf_url,
                    'year': report.get('year')
                })
                
            except Exception as e:
                debug_results.append({
                    'title': report['title'],
                    'original_url': report['url'],
                    'error': str(e)
                })
        
        return jsonify({
            'company': symbol,
            'company_name': company_data.company_name,
            'annual_reports_found': len(company_data.annual_reports),
            'debug_results': debug_results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug-tcs-reports')
def debug_tcs_reports():
    """Debug TCS annual reports specifically"""
    try:
        scraper = EnhancedScreenerScraper(delay=1)
        
        # Find TCS
        company_url = scraper.find_company_by_symbol('TCS')
        if not company_url:
            return jsonify({'error': 'Could not find TCS page'}), 404
        
        # Extract data
        company_data = scraper.extract_concall_data(company_url)
        if not company_data:
            return jsonify({'error': 'Could not extract TCS data'}), 404
        
        # Show all annual reports found
        reports_info = []
        for report in company_data.annual_reports:
            parsed_date = report.get('parsed_date')
            reports_info.append({
                'title': report['title'],
                'url': report['url'],
                'year': report.get('year'),
                'date': report.get('date'),
                'parsed_date': parsed_date.strftime('%Y-%m-%d') if parsed_date else None
            })
        
        return jsonify({
            'company_name': company_data.company_name,
            'total_annual_reports': len(company_data.annual_reports),
            'annual_reports': reports_info
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/version')
def get_version():
    """Check current version and BSE handling"""
    return jsonify({
        'version': '2.1-BSE-Fix',
        'timestamp': datetime.now().isoformat(),
        'bse_handling': 'enabled',
        'features': [
            'BSE URL conversion',
            'Annual report filtering',
            'Enhanced logging'
        ]
    })

@app.route('/api/debug-url', methods=['POST'])
def debug_url():
    """Debug a specific URL"""
    data = request.json or {}
    test_url = data.get('url')
    
    if not test_url:
        return jsonify({'error': 'URL required'}), 400
    
    try:
        scraper = EnhancedScreenerScraper(delay=1)
        
        # Test the URL
        result = scraper.download_document(test_url, 'test.pdf', '/tmp')
        
        return jsonify({
            'url': test_url,
            'success': result,
            'message': 'Check server logs for detailed output'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scraping-stats')
def get_scraping_stats():
    """Get current scraping statistics"""
    return jsonify({
        'is_running': scraping_manager.is_running,
        'total_downloaded': scraping_manager.total_downloaded,
        'results_count': len(scraping_manager.results) if scraping_manager.results else 0,
        'status': 'running' if scraping_manager.is_running else 'idle'
    })

@app.route('/api/reset-stats', methods=['POST'])
def reset_stats():
    """Reset scraping statistics"""
    scraping_manager.total_downloaded = 0
    scraping_manager.results = {}
    return jsonify({'message': 'Statistics reset successfully'})

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