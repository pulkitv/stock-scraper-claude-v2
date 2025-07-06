#!/usr/bin/env python3
"""
Enhanced Screener.in scraper module with date extraction
Fixed version that works with the GUI
"""

import requests
from bs4 import BeautifulSoup, Tag
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
        
        # Find documents with date extraction
        concalls = []
        annual_reports = []
        
        # Look for annual reports section specifically
        # Try to find annual reports in dedicated sections
        annual_report_sections = soup.find_all(['section', 'div'], class_=lambda x: bool(x and ('annual' in x.lower() or 'report' in x.lower())))
        
        # Also look for links with "Financial Year" pattern
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            # Check if it's a Tag element (not NavigableString)
            if not hasattr(link, 'get') or not callable(getattr(link, 'get', None)):
                continue
            
            if isinstance(link, Tag):  # Ensure link is a Tag object
                href = link.get('href')
            else:
                href = None
            if not href:
                continue
            
            text = link.get_text(strip=True)
            
            # Skip very short or empty links
            if len(text) < 5:
                continue
            
            # Check for Financial Year pattern (Annual Reports)
            if any(pattern in text.lower() for pattern in ['financial year', 'fy 20', 'annual report', 'yearly report']):
                # Extract year from Financial Year pattern
                fy_match = re.search(r'financial year\s*(\d{4})', text.lower())
                fy_short_match = re.search(r'fy\s*(\d{4})', text.lower())
                year_match = re.search(r'\b(20\d{2})\b', text)
                
                if fy_match:
                    year = int(fy_match.group(1))
                    date_str = f"FY{year}"
                    parsed_date = datetime(year, 3, 31)  # Assuming March year-end
                elif fy_short_match:
                    year = int(fy_short_match.group(1))
                    date_str = f"FY{year}"
                    parsed_date = datetime(year, 3, 31)
                elif year_match:
                    year = int(year_match.group(1))
                    date_str = f"FY{year}"
                    parsed_date = datetime(year, 3, 31)
                else:
                    date_str, parsed_date, quarter, year = self.extract_date_from_text(text)
                
                annual_reports.append({
                    'title': text,
                    'url': urljoin(self.base_url, str(href)),
                    'type': 'annual_report',
                    'date': date_str,
                    'parsed_date': parsed_date,
                    'quarter': None,
                    'year': year if 'year' in locals() else None
                })
                continue
            
            # Check for concall-related content (but not annual reports)
            elif any(word in text.lower() for word in ['concall', 'transcript', 'presentation', 'earnings call', 'investor call']):
                # Skip if it looks like an annual report
                if any(pattern in text.lower() for pattern in ['annual report', 'financial year', 'yearly report']):
                    continue
                    
                # Extract date information
                date_str, parsed_date, quarter, year = self.extract_date_from_text(text)
                
                doc_type = 'concall'
                if 'transcript' in text.lower():
                    doc_type = 'transcript'
                elif 'presentation' in text.lower():
                    doc_type = 'presentation'
                elif 'earnings' in text.lower():
                    doc_type = 'earnings_call'
                
                concalls.append(ConcallDocument(
                    title=text,
                    url=urljoin(self.base_url, str(href)),
                    doc_type=doc_type,
                    date=date_str,
                    parsed_date=parsed_date,
                    quarter=quarter,
                    year=year
                ))
        
        # Try to find annual reports by looking for specific sections or tabs
        # Look for tabs or sections that might contain annual reports
        tabs = soup.find_all(['a', 'button', 'div'], text=re.compile(r'annual|report|financials', re.I))
        for tab in tabs:
            if isinstance(tab, Tag) and tab.get('href'):
                # Visit the annual reports section
                annual_url = urljoin(self.base_url, str(tab['href']))
                annual_response = self._make_request(annual_url)
                if annual_response:
                    annual_soup = BeautifulSoup(annual_response.content, 'html.parser')
                    annual_links = annual_soup.find_all('a', href=True)
                    
                    for link in annual_links:
                        if isinstance(link, Tag):
                            href = link.get('href')
                            text = link.get_text(strip=True)
                            
                            if len(text) > 5 and any(pattern in text.lower() for pattern in ['financial year', 'fy 20', 'annual report']):
                                # Extract year from Financial Year pattern
                                fy_match = re.search(r'financial year\s*(\d{4})', text.lower())
                                fy_short_match = re.search(r'fy\s*(\d{4})', text.lower())
                                year_match = re.search(r'\b(20\d{2})\b', text)
                                
                                if fy_match:
                                    year = int(fy_match.group(1))
                                    date_str = f"FY{year}"
                                    parsed_date = datetime(year, 3, 31)
                                elif fy_short_match:
                                    year = int(fy_short_match.group(1))
                                    date_str = f"FY{year}"
                                    parsed_date = datetime(year, 3, 31)
                                elif year_match:
                                    year = int(year_match.group(1))
                                    date_str = f"FY{year}"
                                    parsed_date = datetime(year, 3, 31)
                                else:
                                    continue
                                
                                # Check if this report is already in our list
                                if not any(report['url'] == urljoin(self.base_url, str(href)) for report in annual_reports):
                                    annual_reports.append({
                                        'title': text,
                                        'url': urljoin(self.base_url, str(href)),
                                        'type': 'annual_report',
                                        'date': date_str,
                                        'parsed_date': parsed_date,
                                        'quarter': None,
                                        'year': year
                                    })
        
        # Sort by date (newest first) and limit to 5 most recent concalls
        concalls.sort(key=lambda x: x.parsed_date or datetime.min, reverse=True)
        concalls = concalls[:5]  # Keep only the 5 most recent documents
        
        # Sort annual reports by date and limit to 3 most recent
        annual_reports.sort(key=lambda x: x.get('parsed_date') or datetime.min, reverse=True)
        annual_reports = annual_reports[:3]  # Keep only the 3 most recent annual reports
        
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
        
        # Get date info - works with both ConcallDocument and dict-like objects
        date_part = getattr(doc, 'date', None) or doc.get('date', f'doc-{index}') if hasattr(doc, 'get') else f'doc-{index}'
        date_part = str(date_part).replace('/', '-').replace(' ', '-')
        
        # Get document type - works with both ConcallDocument and dict-like objects  
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
        """Download document to specified directory"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(download_dir, exist_ok=True)
            
            # Full file path
            file_path = os.path.join(download_dir, filename)
            
            # Make request
            response = self._make_request(url)
            if not response:
                return False
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            return True
            
        except Exception as e:
            print(f"Download error: {e}")
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

def main():
    """Test the scraper"""
    scraper = EnhancedScreenerScraper(delay=2)
    print("✅ Enhanced Scraper loaded successfully!")
    print("🎯 Ready to use with GUI")

if __name__ == "__main__":
    main()