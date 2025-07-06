#!/usr/bin/env python3
"""
Enhanced launcher for Screener.in GUI Application v2.0
Supports date extraction and smart file naming
"""

import sys
import os
import subprocess

def check_requirements():
    """Check if required packages are installed"""
    required_packages = ['requests', 'beautifulsoup4', 'pandas', 'openpyxl']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    return missing_packages

def install_packages(packages):
    """Install missing packages"""
    print("Installing required packages...")
    for package in packages:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    print("All packages installed successfully!")

def create_enhanced_scraper_module():
    """Create enhanced scraper module if it doesn't exist"""
    scraper_file = "screener_scraper.py"
    
    if not os.path.exists(scraper_file):
        print(f"Creating enhanced {scraper_file}...")
        
        # Create enhanced scraper module with date extraction
        scraper_code = '''#!/usr/bin/env python3
"""
Enhanced Screener.in scraper module with date extraction
This is a simplified version for the GUI with basic date parsing
"""

import requests
from bs4 import BeautifulSoup
import time
import os
import re
from urllib.parse import urljoin
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class ConcallDocument:
    title: str
    url: str
    doc_type: str
    date: Optional[str] = None
    parsed_date: Optional[datetime] = None
    quarter: Optional[str] = None
    year: Optional[int] = None

@dataclass  
class CompanyData:
    company_name: str
    symbol: str
    company_url: str
    concalls: List[ConcallDocument]
    annual_reports: List[dict]

class EnhancedScreenerScraper:
    def __init__(self, delay=2):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.delay = delay
        self.base_url = "https://www.screener.in"
        
        # Basic date patterns
        self.date_patterns = [
            r'Q([1-4])\\s*FY\\s*(\\d{2,4})',  # Q1 FY2024
            r'(\\d{1,2})[/-](\\d{1,2})[/-](\\d{2,4})',  # DD/MM/YYYY
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\\s*(\\d{2,4})',  # Mon YYYY
        ]
        
        self.month_names = {
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
    
    def _make_request(self, url):
        """Make request with delay"""
        time.sleep(self.delay)
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response
        except:
            return None
    
    def extract_date_from_text(self, text: str) -> tuple:
        """Basic date extraction from text"""
        text_lower = text.lower().strip()
        
        # Look for quarter patterns
        quarter_match = re.search(r'q([1-4])\\s*fy\\s*(\\d{2,4})', text_lower)
        if quarter_match:
            quarter = f"Q{quarter_match.group(1)}"
            year = int(quarter_match.group(2))
            if year < 100:
                year = 2000 + year
            return f"{quarter} FY{year}", None, quarter, year
        
        # Look for month patterns  
        month_match = re.search(r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\\s*(\\d{2,4})', text_lower)
        if month_match:
            month_name = month_match.group(1)
            year = int(month_match.group(2))
            if year < 100:
                year = 2000 + year
            try:
                month = self.month_names[month_name]
                parsed_date = datetime(year, month, 1)
                return parsed_date.strftime("%b-%Y"), parsed_date, None, year
            except:
                pass
        
        # Look for year only
        year_match = re.search(r'\\b(20\\d{2})\\b', text)
        if year_match:
            year = int(year_match.group(1))
            return f"FY{year}", None, None, year
        
        return None, None, None, None
    
    def find_company_by_symbol(self, symbol: str) -> Optional[str]:
        """Find company URL by symbol"""
        possible_urls = [
            f"{self.base_url}/company/{symbol.upper()}/",
            f"{self.base_url}/company/{symbol.upper()}/consolidated/",
        ]
        
        for url in possible_urls:
            response = self._make_request(url)
            if response and response.status_code == 200:
                return url
        return None
    
    def extract_concall_data(self, company_url: str) -> CompanyData:
        """Extract data from company page with date parsing"""
        response = self._make_request(company_url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract company info
        h1_tag = soup.find('h1')
        company_name = h1_tag.get_text(strip=True) if h1_tag else ""
        symbol = company_url.split('/company/')[-1].split('/')[0]
        
        # Find documents with date extraction
        concalls = []
        annual_reports = []
        
        # Look for PDF and document links
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            href = link.get('href')
            text = link.get_text(strip=True)
            
            # Skip very short or empty links
            if len(text) < 5:
                continue
            
            # Check for concall-related content
            if any(word in text.lower() for word in ['concall', 'transcript', 'presentation', 'earnings', 'result']):
                # Extract date information
                date_str, parsed_date, quarter, year = self.extract_date_from_text(text)
                
                doc_type = 'concall'
                if 'transcript' in text.lower():
                    doc_type = 'transcript'
                elif 'presentation' in text.lower():
                    doc_type = 'presentation'
                
                concalls.append(ConcallDocument(
                    title=text,
                    url=urljoin(self.base_url, href),
                    doc_type=doc_type,
                    date=date_str,
                    parsed_date=parsed_date,
                    quarter=quarter,
                    year=year
                ))
            elif href.endswith('.pdf'):
                date_str, parsed_date, quarter, year = self.extract_date_from_text(text)
                annual_reports.append({
                    'title': text,
                    'url': urljoin(self.base_url, href),
                    'type': 'pdf',
                    'date': date_str,
                    'year': year
                })
        
        # Sort by date (newest first)
        concalls.sort(key=lambda x: x.parsed_date or datetime.min, reverse=True)
        
        return CompanyData(
            company_name=company_name,
            symbol=symbol,
            company_url=company_url,
            concalls=concalls,
            annual_reports=annual_reports
        )
    
    def generate_filename(self, company_symbol: str, doc: ConcallDocument, index: int) -> str:
        """Generate filename with date information"""
        parts = [company_symbol]
        
        # Add date information
        if doc.date:
            date_part = doc.date.replace('/', '-').replace(' ', '-')
            parts.append(date_part)
        else:
            parts.append(f"doc-{index+1}")
        
        # Add document type
        parts.append(doc.doc_type)
        
        # Clean filename
        filename = '_'.join(parts) + '.pdf'
        filename = re.sub(r'[<>:"/\\\\|?*]', '_', filename)
        
        return filename
    
    def download_document(self, doc_url: str, filename: str, download_dir="downloads"):
        """Download document"""
        try:
            os.makedirs(download_dir, exist_ok=True)
            response = self._make_request(doc_url)
            if not response:
                return False
            
            filepath = os.path.join(download_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(response.content)
            return True
        except:
            return False
    
    def scrape_company_data(self, symbol: str, download_docs=True):
        """Main scraping method"""
        company_url = self.find_company_by_symbol(symbol)
        if not company_url:
            return None
        
        company_data = self.extract_concall_data(company_url)
        return company_data

# For backward compatibility
ScreenerScraper = EnhancedScreenerScraper
'''
        
        with open(scraper_file, 'w') as f:
            f.write(scraper_code)
        
        print(f"Created enhanced {scraper_file}")

def create_requirements_file():
    """Create requirements.txt if it doesn't exist"""
    requirements_file = "requirements.txt"
    
    if not os.path.exists(requirements_file):
        print(f"Creating {requirements_file}...")
        
        requirements_content = '''requests>=2.25.1
beautifulsoup4>=4.9.3
pandas>=1.3.0
openpyxl>=3.0.7
lxml>=4.6.3'''
        
        with open(requirements_file, 'w') as f:
            f.write(requirements_content)
        
        print(f"Created {requirements_file}")

def create_readme_file():
    """Create README.md if it doesn't exist"""
    readme_file = "README.md"
    
    if not os.path.exists(readme_file):
        print(f"Creating {readme_file}...")
        
        readme_content = '''# Screener.in Enhanced Scraper v2.0

🚀 **Enhanced with Smart Date Extraction & Chronological File Organization**

## Features
- ✅ Automatic date extraction from document titles
- ✅ Quarter-aware file naming (Q1-FY2024, Q2-FY2023)
- ✅ Chronological file organization  
- ✅ Preview functionality
- ✅ Enhanced GUI with real-time progress
- ✅ Multiple document type detection

## Quick Start
1. Run: `python gui_launcher.py`
2. Enter company symbols (e.g., RELIANCE, TCS, INFY)
3. Click "Preview Files" to see date extraction
4. Start Enhanced Scraping

## File Naming Examples
- TCS_Q1-FY2024_transcript.pdf
- RELIANCE_Mar-2024_presentation.pdf  
- INFY_FY2023_annual_report.pdf

## Requirements
- Python 3.7+
- Internet connection
- 50MB+ free disk space

Created for educational and research purposes.
Please use responsibly and respect server resources.'''
        
        with open(readme_file, 'w') as f:
            f.write(readme_content)
        
        print(f"Created {readme_file}")

def main():
    print("🚀 Enhanced Screener.in GUI Launcher v2.0")
    print("=" * 50)
    print("✨ New Features:")
    print("   • Smart date extraction from document titles")
    print("   • Quarter-aware file naming (Q1-FY2024)")
    print("   • Chronological file organization") 
    print("   • Enhanced document type detection")
    print("   • Preview functionality")
    print("=" * 50)
    
    # Check and install requirements
    missing = check_requirements()
    if missing:
        print(f"📦 Missing packages: {', '.join(missing)}")
        try:
            install_packages(missing)
        except Exception as e:
            print(f"❌ Error installing packages: {e}")
            print("Please install manually with: pip install requests beautifulsoup4 pandas openpyxl")
            return
    
    # Create enhanced scraper module if needed
    create_enhanced_scraper_module()
    
    # Create additional project files
    create_requirements_file()
    create_readme_file()
    
    # Check if GUI file exists
    gui_file = "screener_gui.py"
    if not os.path.exists(gui_file):
        print(f"❌ Error: {gui_file} not found!")
        print("Please make sure screener_gui.py is in the same directory.")
        print("\n📋 Required files:")
        print("   • screener_scraper.py (Core scraper)")
        print("   • screener_gui.py (GUI interface)")
        print("   • gui_launcher.py (This launcher)")
        print("   • requirements.txt (Auto-created)")
        return
    
    print("✅ All requirements satisfied!")
    print("🎯 Starting enhanced GUI application...")
    print("\n📊 Expected filename format:")
    print("   📄 SYMBOL_Date_Type.pdf")
    print("   📄 Example: TCS_Q1-FY2024_transcript.pdf")
    print("   📄 Example: RELIANCE_Mar-2024_presentation.pdf")
    print("   📄 Example: INFY_FY2023_annual_report.pdf")
    print("\n🔍 New Features Available:")
    print("   • Preview Files - See what will be downloaded")
    print("   • Date Extraction - Smart parsing from titles")
    print("   • Enhanced Progress - Real-time date feedback")
    print("   • Help System - Complete usage guides")
    print("\n🚀 Launching Enhanced GUI...")
    
    try:
        # Import and run the enhanced GUI
        import importlib.util
        spec = importlib.util.spec_from_file_location("screener_gui", gui_file)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load module from {gui_file}")
        gui_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gui_module)
        
        # Start the GUI
        gui_module.main()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please ensure all required files are in the same directory.")
    except Exception as e:
        print(f"❌ Error starting GUI: {e}")
        print("Please check the error and try again.")
        print("\n🛠️  Troubleshooting:")
        print("   1. Ensure all 4 files are in the same folder")
        print("   2. Check Python version (3.7+ required)")
        print("   3. Verify internet connection")
        print("   4. Try running: pip install -r requirements.txt")

if __name__ == "__main__":
    main()