#!/usr/bin/env python3
"""
Enhanced Screener.in scraper module with date extraction
Fixed version that works with the GUI
"""

import requests
import time
import os
from urllib.parse import parse_qs, urlparse
from bs4 import BeautifulSoup, Tag
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
            r'Q([1-4])\s*FY\s*(\d{2,4})',  # Q1 FY2024
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',  # DD/MM/YYYY
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*(\d{2,4})',  # Mon YYYY
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
        quarter_match = re.search(r'q([1-4])\s*fy\s*(\d{2,4})', text_lower)
        if quarter_match:
            quarter = f"Q{quarter_match.group(1)}"
            year = int(quarter_match.group(2))
            if year < 100:
                year = 2000 + year
            return f"{quarter} FY{year}", None, quarter, year
        
        # Look for month patterns  
        month_match = re.search(r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*(\d{2,4})', text_lower)
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
        year_match = re.search(r'\b(20\d{2})\b', text)
        if year_match:
            year = int(year_match.group(1))
            return f"FY{year}", None, None, year
        
        return None, None, None, None
    
    def find_company_by_symbol(self, symbol: str) -> Optional[str]:
        """Find company URL by symbol"""
        # Try different URL patterns that screener.in might use
        possible_urls = [
            f"{self.base_url}/company/{symbol}/",
            f"{self.base_url}/company/{symbol.lower()}/",
            f"{self.base_url}/company/{symbol.upper()}/",
            f"{self.base_url}/company/{symbol}/consolidated/",
        ]
        
        for url in possible_urls:
            response = self._make_request(url)
            if response and response.status_code == 200:
                return url
        
        # If direct URL doesn't work, try search
        search_url = f"{self.base_url}/search/?q={symbol}"
        response = self._make_request(search_url)
        if response:
            soup = BeautifulSoup(response.content, 'html.parser')
            # Look for company links in search results
            for link in soup.find_all('a', href=True):
                href = link['href'] if isinstance(link, Tag) and 'href' in link.attrs else ''
                if isinstance(link, Tag) and href and '/company/' in href:
                    company_url = urljoin(self.base_url, str(link['href']))
                    return company_url
        
        return None
    
    def extract_concall_data(self, company_url: str) -> Optional[CompanyData]:
        """Extract data from company page with date parsing"""
        response = self._make_request(company_url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract company info
        h1_tag = soup.find('h1')
        company_name = h1_tag.get_text(strip=True) if h1_tag else ""
        symbol = company_url.split('/company/')[-1].split('/')[0]
        
        # Initialize lists
        concalls = []
        annual_reports = []
        
        # FIND THE SPECIFIC ANNUAL REPORTS SECTION
        print(f"🔍 Looking for dedicated annual reports section...")
        
        # Look for the specific annual reports section
        annual_reports_section = soup.find('div', class_='documents annual-reports')
        if not annual_reports_section:
            # Try alternative selectors
            annual_reports_section = soup.find('div', {'class': lambda x: bool(x and 'annual-reports' in x)})
        
        if annual_reports_section and isinstance(annual_reports_section, Tag):
            print(f"✅ Found dedicated annual reports section!")
            
            # Find all links within this section
            annual_links = annual_reports_section.find_all('a', href=True)
            
            for link in annual_links:
                if not isinstance(link, Tag):
                    continue
                    
                href = link.get('href')
                if not href:
                    continue
                    
                text = link.get_text(strip=True)
                
                # Skip empty links
                if len(text) < 5:
                    continue
                
                # Check if it's an annual report link (BSE/NSE URLs)
                if any(domain in str(href) for domain in ['bseindia.com', 'nseindia.com', 'archives.nseindia.com']):
                    print(f"🔍 Found annual report link: {text}")
                    print(f"🔗 URL: {href}")
                    
                    # Extract year from text
                    year = None
                    text_lower = text.lower()
                    
                    # Enhanced year extraction for "Financial Year YYYY" pattern
                    patterns = [
                        r'financial year\s+(\d{4})',     # "Financial Year 2024"
                        r'fy\s+(\d{4})',                 # "FY 2024"
                        r'year\s+(\d{4})',               # "Year 2024"
                        r'\b(\d{4})\b',                  # Any 4-digit year
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, text_lower)
                        if match:
                            year = int(match.group(1))
                            break
                    
                    print(f"📅 Extracted year: {year}")
                    
                    # Build full URL
                    if str(href).startswith('http'):
                        full_url = str(href)
                    else:
                        full_url = urljoin(self.base_url, str(href))
                    
                    # Add to annual reports
                    annual_reports.append({
                        'title': text,
                        'url': full_url,
                        'type': 'annual_report',
                        'date': f"FY{year}" if year else "FY Unknown",
                        'parsed_date': datetime(year, 3, 31) if year else datetime.min,
                        'quarter': None,
                        'year': year
                    })
        else:
            print(f"❌ Could not find dedicated annual reports section")
        
        # FIND THE SPECIFIC CONCALLS SECTION
        print(f"🔍 Looking for dedicated concalls section...")
        
        # Look for the specific concalls section
        concalls_section = soup.find('div', class_='documents concalls')
        if not concalls_section:
            # Try alternative selectors
            concalls_section = soup.find('div', {'class': lambda x: bool(x and 'concalls' in x)})
        
        if concalls_section and isinstance(concalls_section, Tag):
            print(f"✅ Found dedicated concalls section!")
            
            # Find all list items within this section
            concall_items = concalls_section.find_all('li')
            
            for item in concall_items:
                if not isinstance(item, Tag):
                    continue
                
                # Extract date from the date div
                date_div = item.find('div', class_='ink-600')
                if date_div:
                    date_text = date_div.get_text(strip=True)
                    print(f"📅 Found concall date: {date_text}")
                    
                    # Parse date (format: "Apr 2025", "Jan 2024", etc.)
                    date_str, parsed_date, quarter, year = self.extract_date_from_text(date_text)
                    
                    # Find all concall links in this item
                    concall_links = item.find_all('a', class_='concall-link')
                    
                    for link in concall_links:
                        if not isinstance(link, Tag):
                            continue
                        
                        href = link.get('href')
                        if not href:
                            continue
                        
                        text = link.get_text(strip=True)
                        
                        # Skip empty links and button elements
                        if len(text) < 2:
                            continue
                        
                        # Skip modal buttons (they don't have href starting with http)
                        if not str(href).startswith('http') and not str(href).startswith('/'):
                            continue
                        
                        # Determine document type based on text
                        doc_type = 'concall'
                        if text.lower() == 'transcript':
                            doc_type = 'transcript'
                        elif text.lower() == 'ppt':
                            doc_type = 'presentation'
                        elif text.lower() == 'rec':
                            doc_type = 'recording'
                        elif 'presentation' in text.lower():
                            doc_type = 'presentation'
                        elif 'transcript' in text.lower():
                            doc_type = 'transcript'
                        
                        # Build full URL
                        if str(href).startswith('http'):
                            full_url = str(href)
                        else:
                            full_url = urljoin(self.base_url, str(href))
                        
                        print(f"🔍 Found concall document: {text} ({doc_type})")
                        print(f"🔗 URL: {full_url}")
                        
                        # Create concall document with the date from this section
                        concalls.append(ConcallDocument(
                            title=f"{date_text} - {text}",
                            url=full_url,
                            doc_type=doc_type,
                            date=date_str or date_text,
                            parsed_date=parsed_date,
                            quarter=quarter,
                            year=year
                        ))
        else:
            print(f"❌ Could not find dedicated concalls section")

        # Sort and limit results
        concalls.sort(key=lambda x: x.parsed_date or datetime.min, reverse=True)
        concalls = concalls[:20]  # Get 20 concalls to ensure we have enough quarters
        
        # Sort annual reports by date (most recent first)
        print(f"📊 Found {len(annual_reports)} annual reports from dedicated section:")
        for i, report in enumerate(annual_reports):
            print(f"  {i+1}. {report['title']} (Year: {report.get('year', 'Unknown')})")
        
        annual_reports.sort(key=lambda x: x.get('parsed_date') or datetime.min, reverse=True)
        annual_reports = annual_reports[:5]  # Keep top 5 most recent
        
        print(f"📊 Found {len(concalls)} concall documents from dedicated section:")
        for i, concall in enumerate(concalls):
            print(f"  {i+1}. {concall.title} ({concall.doc_type})")
        
        print(f"📊 Keeping {len(annual_reports)} most recent annual reports:")
        for i, report in enumerate(annual_reports):
            print(f"  {i+1}. {report['title']} (Year: {report.get('year', 'Unknown')})")
        
        return CompanyData(
            company_name=company_name,
            symbol=symbol,
            company_url=company_url,
            concalls=concalls,
            annual_reports=annual_reports
        )
    
    def generate_filename(self, company: str, doc, index: int) -> str:
        """Generate filename for document with date and type"""
        # Clean company symbol
        company_clean = company.replace('/', '_').replace('\\', '_')
        
        # Get date info - works with both ConcallDocument and doc-like objects
        date_part = getattr(doc, 'date', None) or doc.get('date', f'doc-{index}') if hasattr(doc, 'get') else f'doc-{index}'
        date_part = str(date_part).replace('/', '-').replace(' ', '-')
        
        # Get document type - works with both ConcallDocument and doc-like objects  
        doc_type = getattr(doc, 'doc_type', None) or doc.get('doc_type', 'document') if hasattr(doc, 'get') else 'document'
        doc_type = str(doc_type).lower()
        
        # Fix document type naming for better differentiation
        if doc_type == 'document' and hasattr(doc, 'title'):
            title_lower = str(getattr(doc, 'title', '')).lower()
            if 'annual' in title_lower or 'financial year' in title_lower:
                doc_type = 'annual_report'
            elif 'transcript' in title_lower:
                doc_type = 'transcript'
            elif 'presentation' in title_lower:
                doc_type = 'presentation'
        
        # Special handling for annual reports with Financial Year naming
        if doc_type == 'annual_report' and 'fy' in date_part.lower():
            # Keep the FY format for annual reports
            pass
        elif doc_type == 'annual_report' and not date_part.startswith('FY'):
            # Add FY prefix if it's an annual report but doesn't have it
            if date_part.startswith('doc-'):
                date_part = f'FY{2024-index}'  # Estimate year based on index
        
        # Get file extension from URL or default to pdf
        url = getattr(doc, 'url', None) or doc.get('url', '') if hasattr(doc, 'get') else ''
        url_lower = str(url).lower()
        if '.pdf' in url_lower:
            ext = 'pdf'
        elif '.ppt' in url_lower:
            ext = 'ppt'
        elif '.doc' in url_lower:
            ext = 'doc'
        else:
            ext = 'pdf'
        
        return f"{company_clean}_{date_part}_{doc_type}.{ext}"
    
    def download_document(self, url: str, filename: str, download_dir: str) -> bool:
        """Download document from URL with enhanced BSE handling"""
        try:
            print(f"🔍 Attempting to download: {url}")
            print(f"📄 Filename: {filename}")
            
            # Create download directory
            os.makedirs(download_dir, exist_ok=True)
            file_path = os.path.join(download_dir, filename)
            
            # Handle BSE URLs with direct redirect approach
            if 'bseindia.com' in url and 'AnnPdfOpen.aspx' in url:
                print("🎯 BSE URL detected!")
                return self._download_bse_document(url, file_path)
            
            # Handle regular URLs
            print("⏰ Making request to:", url)
            start_time = time.time()
            
            response = self.session.get(url, stream=True, timeout=30)
            elapsed_time = time.time() - start_time
            
            print(f"⏰ Request completed in {elapsed_time:.2f} seconds")
            print(f"📊 Response status: {response.status_code}")
            print(f"📊 Content-Type: {response.headers.get('content-type', 'unknown')}")
            print(f"📊 Final URL: {response.url}")
            
            if response.status_code == 200:
                with open(file_path, 'wb') as f:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
            
                print(f"✅ Downloaded: {filename} ({downloaded} bytes)")
                time.sleep(self.delay)
                return True
            else:
                print(f"❌ HTTP {response.status_code}: {response.reason}")
                return False
                
        except Exception as e:
            print(f"❌ Download error: {str(e)}")
            return False

    def _download_bse_document(self, url: str, file_path: str) -> bool:
        """Handle BSE document downloads with advanced bypass methods"""
        try:
            print("🔄 BSE URL detected, applying advanced bypass methods...")
            
            # Extract the Pname parameter from the URL
            from urllib.parse import parse_qs, urlparse
            
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            
            if 'Pname' not in query_params:
                print("❌ No Pname parameter found in BSE URL")
                return False
            
            pname = query_params['Pname'][0]
            print(f"📋 Extracted Pname: {pname}")
            
            # Clean up the Pname (remove backslashes and other issues)
            clean_pname = pname.replace('\\', '').replace('%5C', '')
            print(f"🧹 Cleaned Pname: {clean_pname}")
            
            # Method 1: Try browser automation approach
            print("🤖 Trying browser automation method...")
            if self._download_bse_with_selenium(url, clean_pname, file_path):
                return True
            
            # Method 2: Try session-based approach with proper BSE flow
            print("🔄 Trying session-based BSE flow...")
            if self._download_bse_with_proper_session(url, clean_pname, file_path):
                return True
            
            # Method 3: Try direct PDF construction with verification
            print("🔄 Trying direct PDF verification...")
            if self._download_bse_direct_verified(clean_pname, file_path):
                return True
            
            # Method 4: Try with request intercepting
            print("🔄 Trying request interception method...")
            if self._download_bse_with_interception(url, clean_pname, file_path):
                return True
            
            print("❌ All BSE download methods failed - BSE has strong anti-bot protection")
            return False
            
        except Exception as e:
            print(f"❌ BSE bypass error: {str(e)}")
            return False

    def _download_bse_with_selenium(self, url: str, clean_pname: str, file_path: str) -> bool:
        """Try BSE download using Selenium browser automation"""
        try:
            # Try to import selenium
            try:
                from selenium import webdriver
                from selenium.webdriver.chrome.options import Options
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                import time
            except ImportError:
                print("⚠️ Selenium not installed, skipping browser automation method")
                return False
            
            print("🤖 Starting browser automation...")
            
            # Setup Chrome options
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # Run in background
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
            
            # Set download preferences
            download_dir = os.path.dirname(file_path)
            prefs = {
                "download.default_directory": download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            try:
                # Initialize Chrome driver
                driver = webdriver.Chrome(options=chrome_options)
                driver.set_page_load_timeout(30)
                
                print("🌐 Navigating to BSE page...")
                driver.get(url)
                
                # Wait for page to load
                time.sleep(5)
                
                # Check if we got redirected to the PDF
                current_url = driver.current_url
                print(f"📍 Current URL: {current_url}")
                
                if current_url.endswith('.pdf') or 'xml-data/corpfiling' in current_url:
                    print("✅ Browser was redirected to PDF, downloading...")
                    
                    # Use requests to download the PDF from the redirected URL
                    response = requests.get(current_url, stream=True, timeout=30)
                    if response.status_code == 200:
                        with open(file_path, 'wb') as f:
                            downloaded = 0
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    downloaded += len(chunk)
                        
                        if downloaded > 1000:
                            print(f"✅ Selenium download successful: {os.path.basename(file_path)} ({downloaded} bytes)")
                            driver.quit()
                            return True
                
                # Try to find download links on the page
                download_links = driver.find_elements(By.XPATH, "//a[contains(@href, '.pdf') or contains(text(), 'Download') or contains(text(), 'PDF')]")
                
                for link in download_links[:3]:  # Try first 3 links
                    try:
                        href = link.get_attribute('href')
                        if href and '.pdf' in href:
                            print(f"🔗 Found download link: {href}")
                            
                            response = requests.get(href, stream=True, timeout=30)
                            if response.status_code == 200:
                                with open(file_path, 'wb') as f:
                                    downloaded = 0
                                    for chunk in response.iter_content(chunk_size=8192):
                                        if chunk:
                                            f.write(chunk)
                                            downloaded += len(chunk)
                                
                                if downloaded > 1000:
                                    print(f"✅ Selenium link download successful: {os.path.basename(file_path)} ({downloaded} bytes)")
                                    driver.quit()
                                    return True
                    except Exception as e:
                        print(f"⚠️ Link attempt failed: {str(e)}")
                        continue
                
                # Clean up driver and return False if no downloads succeeded
                driver.quit()
                return False
            
            except Exception as e:
                print(f"❌ Selenium browser error: {str(e)}")
                if 'driver' in locals():
                    driver.quit()
                return False
            
        except Exception as e:
            print(f"❌ Selenium method failed: {str(e)}")
            return False

    def _download_bse_with_proper_session(self, url: str, clean_pname: str, file_path: str) -> bool:
        """Try BSE download with proper session establishment"""
        try:
            print("🔄 Establishing proper BSE session...")
            
            # Create a new session that mimics browser behavior
            bse_session = requests.Session()
            
            # Set comprehensive headers
            bse_session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0',
                'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"'
            })
            
            # Step 1: Visit BSE homepage to establish session
            print("🏠 Visiting BSE homepage...")
            homepage_response = bse_session.get("https://www.bseindia.com", timeout=15)
            if homepage_response.status_code != 200:
                print(f"❌ Failed to load BSE homepage: {homepage_response.status_code}")
                return False
            
            # Step 2: Visit a company page to get proper cookies
            print("🏢 Visiting company section...")
            company_response = bse_session.get("https://www.bseindia.com/stock-share-price/", timeout=15)
            
            # Step 3: Now try the annual report with proper referrer
            print("📄 Attempting to access annual report...")
            bse_session.headers.update({
                'Referer': 'https://www.bseindia.com/stock-share-price/'
            })
            
            # Try the original URL first
            response = bse_session.get(url, allow_redirects=True, timeout=30)
            print(f"📊 Response status: {response.status_code}")
            print(f"📊 Final URL: {response.url}")
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                
                if 'application/pdf' in content_type:
                    with open(file_path, 'wb') as f:
                        downloaded = 0
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                    
                    if downloaded > 1000:
                        print(f"✅ BSE session download successful: {os.path.basename(file_path)} ({downloaded} bytes)")
                        return True
            
                # If we got HTML, try to find the actual PDF link
                if 'text/html' in content_type:
                    print("📄 Got HTML response, looking for PDF link...")
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for iframe or embed with PDF
                    for element in soup.find_all(['iframe', 'embed'], src=True):
                        if not isinstance(element, Tag):
                            continue
                            src = element.get('src')
                        if src and clean_pname in str(src):
                            print(f"🎯 Found PDF in iframe: {src}")
                            
                            if not str(src).startswith('http'):
                                src = f"https://www.bseindia.com{str(src)}"
                            
                            pdf_response = bse_session.get(src, stream=True, timeout=30)
                            if pdf_response.status_code == 200:
                                with open(file_path, 'wb') as f:
                                    downloaded = 0
                                    for chunk in pdf_response.iter_content(chunk_size=8192):
                                        if chunk:
                                            f.write(chunk)
                                            downloaded += len(chunk)
                                
                                if downloaded > 1000:
                                    print(f"✅ BSE iframe download successful: {os.path.basename(file_path)} ({downloaded} bytes)")
                                    return True
            
            return False
            
        except Exception as e:
            print(f"❌ BSE session method failed: {str(e)}")
            return False

    def _download_bse_direct_verified(self, clean_pname: str, file_path: str) -> bool:
        """Try direct BSE download with multiple verification attempts"""
        try:
            # Construct various possible direct URLs
            direct_urls = [
                f"https://www.bseindia.com/xml-data/corpfiling/AttachHis/{clean_pname}",
                f"https://bseindia.com/xml-data/corpfiling/AttachHis/{clean_pname}",
                f"https://www.bseindia.com/corpfiling/AttachHis/{clean_pname}",
                f"https://www.bseindia.com/download/corpfiling/{clean_pname}",
            ]
            
            for i, direct_url in enumerate(direct_urls, 1):
                print(f"🔄 Direct attempt {i}: {direct_url}")
                
                try:
                    # Create session with different characteristics for each attempt
                    session = requests.Session()
                    
                    if i == 1:
                        # Standard browser
                        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
                    elif i == 2:
                        # Firefox
                        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
                    elif i == 3:
                        # Safari
                        user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
                    else:
                        # Mobile
                        user_agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15'
                    
                    session.headers.update({
                        'User-Agent': user_agent,
                        'Accept': 'application/pdf,application/octet-stream,*/*',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Connection': 'keep-alive',
                        'Cache-Control': 'no-cache'
                    })
                    
                    # Add delay between attempts
                    time.sleep(2)
                    
                    response = session.get(direct_url, stream=True, timeout=20)
                    print(f"📊 Status: {response.status_code} | Content-Type: {response.headers.get('content-type', 'unknown')}")
                    
                    if response.status_code == 200:
                        content_type = response.headers.get('content-type', '').lower()
                        content_length = response.headers.get('content-length', '0')
                        
                        # Check if it looks like a valid PDF
                        if ('application/pdf' in content_type or 
                            response.url.endswith('.pdf') or 
                            int(content_length) > 10000):
                            
                            with open(file_path, 'wb') as f:
                                downloaded = 0
                                for chunk in response.iter_content(chunk_size=8192):
                                    if chunk:
                                        f.write(chunk)
                                        downloaded += len(chunk)
                            
                            # Verify the downloaded file
                            if downloaded > 1000:
                                # Quick check if it's actually a PDF
                                with open(file_path, 'rb') as f:
                                    header = f.read(4)
                                    if header.startswith(b'%PDF'):
                                        print(f"✅ Direct verified download successful: {os.path.basename(file_path)} ({downloaded} bytes)")
                                        return True
                                    else:
                                        print(f"⚠️ Downloaded file is not a valid PDF")
                                        os.remove(file_path) if os.path.exists(file_path) else None
                
                except Exception as e:
                    print(f"⚠️ Direct attempt {i} failed: {str(e)}")
                    continue
            
            return False
        
        except Exception as e:
            print(f"❌ Direct verified method failed: {str(e)}")
            return False

    def _download_bse_with_interception(self, url: str, clean_pname: str, file_path: str) -> bool:
        """Try BSE download by intercepting the actual request flow"""
        try:
            print("🕵️ Attempting request interception method...")
            
            # Method: Try to replicate the exact request flow that BSE expects
            session = requests.Session()
            
            # Step 1: Get the page that contains the link
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            })
            
            # Try to find the company page that contains this annual report
            symbol = 'INFY'  # Extract from context or pass as parameter
            company_page = f"https://www.bseindia.com/stock-share-price/infosys-ltd/infy/500209/"
            
            print(f"🏢 Visiting company page: {company_page}")
            company_response = session.get(company_page, timeout=15)
            
            if company_response.status_code == 200:
                print("✅ Company page loaded successfully")
                
                # Update headers to include referrer
                session.headers.update({
                    'Referer': company_page
                })
                
                # Now try the annual report URL
                response = session.get(url, allow_redirects=True, stream=True, timeout=30)
                print(f"📊 Annual report response: {response.status_code}")
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '').lower()
                    
                    if 'application/pdf' in content_type:
                        with open(file_path, 'wb') as f:
                            downloaded = 0
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    downloaded += len(chunk)
                    
                        if downloaded > 1000:
                            print(f"✅ Interception download successful: {os.path.basename(file_path)} ({downloaded} bytes)")
                            return True
            
            return False
            
        except Exception as e:
            print(f"❌ Interception method failed: {str(e)}")
            return False
    
    def scrape_company_data(self, symbol: str, download_docs=True):
        """Main scraping method"""
        company_url = self.find_company_by_symbol(symbol)
        if not company_url:
            return None
        
        company_data = self.extract_concall_data(company_url)
        return company_data
    
    def get_actual_pdf_link(self, page_url: str) -> Optional[str]:
        """Get the actual PDF download link from a page that contains the link"""
        try:
            print(f"🔍 Looking for PDF link in page: {page_url}")
            
            response = self._make_request(page_url)
            if not response:
                return None
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for direct PDF links
            pdf_links = []
            
            # Method 1: Look for links with .pdf in href
            for link in soup.find_all('a', href=True):
                if not isinstance(link, Tag):
                    continue
                href = link.get('href')
                if href and '.pdf' in str(href).lower():
                    if str(href).startswith('http'):
                        pdf_links.append(str(href))
                    else:
                        pdf_links.append(urljoin(self.base_url, str(href)))
            
            # Method 2: Look for links with text containing "download", "pdf", etc.
            for link in soup.find_all('a', href=True):
                if not isinstance(link, Tag):
                    continue
                text = link.get_text(strip=True).lower()
                if any(word in text for word in ['download', 'pdf', 'view', 'open']):
                    href = link.get('href')
                    if href:
                        if str(href).startswith('http'):
                            pdf_links.append(str(href))
                        else:
                            pdf_links.append(urljoin(self.base_url, str(href)))
            
            # Method 3: Look for embed or iframe tags that might contain PDF
            for embed in soup.find_all(['embed', 'iframe'], src=True):
                if not isinstance(embed, Tag):
                    continue
                src = embed.get('src')
                if src and '.pdf' in str(src).lower():
                    if str(src).startswith('http'):
                        pdf_links.append(str(src))
                    else:
                        pdf_links.append(urljoin(self.base_url, str(src)))
            
            # Method 4: Look for script tags that might contain PDF URLs
            for script in soup.find_all('script'):
                script_text = script.get_text()
                if script_text:
                    import re
                    pdf_matches = re.findall(r'https?://[^\s"\']+\.pdf', script_text, re.IGNORECASE)
                    pdf_links.extend(pdf_matches)
            
            # Remove duplicates and filter valid links
            unique_pdf_links = list(set(pdf_links))
            
            print(f"📄 Found {len(unique_pdf_links)} potential PDF links")
            for i, link in enumerate(unique_pdf_links):
                print(f"  {i+1}. {link}")
            
            # Return the first valid PDF link
            for pdf_link in unique_pdf_links:
                if pdf_link and pdf_link.startswith('http'):
                    return pdf_link
            
            return None
            
        except Exception as e:
            print(f"❌ Error getting PDF link: {e}")
            return None

# For backward compatibility
ScreenerScraper = EnhancedScreenerScraper

def main():
    """Test the scraper"""
    scraper = EnhancedScreenerScraper(delay=2)
    print("✅ Enhanced Scraper loaded successfully!")
    print("🎯 Ready to use with GUI")

if __name__ == "__main__":
    main()