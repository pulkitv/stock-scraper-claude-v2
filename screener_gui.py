#!/usr/bin/env python3
"""
Enhanced Screener.in GUI Application v2.0
Shows date information and improved file organization
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
import os
import json
from datetime import datetime
import webbrowser
from pathlib import Path

# Define fallback classes first
class FallbackScreenerScraper:
    def __init__(self, delay=2):
        self.delay = delay
    
    def find_company_by_symbol(self, symbol):
        print(f"❌ Fallback scraper - cannot find {symbol}")
        return None
    
    def extract_concall_data(self, url):
        print(f"❌ Fallback scraper - cannot extract data from {url}")
        return None
    
    def generate_filename(self, company, doc, index):
        """Generate filename for document"""
        doc_type = getattr(doc, 'doc_type', 'document')
        date_info = getattr(doc, 'date', f'doc-{index+1}')
        return f"{company}_{date_info}_{doc_type}.pdf"
    
    def download_document(self, url, filename, download_dir):
        """Download document (fallback implementation)"""
        print(f"❌ Fallback scraper - cannot download {filename}")
        return False

class FallbackCompanyData:
    def __init__(self, company_name="", symbol="", company_url="", concalls=None, annual_reports=None):
        self.company_name = company_name
        self.symbol = symbol
        self.company_url = company_url
        self.concalls = concalls or []
        self.annual_reports = annual_reports or []

class FallbackConcallDocument:
    def __init__(self, doc_type="", date="", url="", title=""):
        self.doc_type = doc_type
        self.date = date
        self.url = url
        self.title = title

# Import our enhanced scraper with fallback
try:
    from screener_scraper import EnhancedScreenerScraper, CompanyData, ConcallDocument
    print("✅ Successfully imported EnhancedScreenerScraper")
    # Store the imported classes for use
    ScraperConcallDocument = ConcallDocument
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Using fallback classes...")
    
    # Use the fallback classes
    EnhancedScreenerScraper = FallbackScreenerScraper
    CompanyData = FallbackCompanyData
    ConcallDocument = FallbackConcallDocument
    ScraperConcallDocument = FallbackConcallDocument

class EnhancedScreenerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Screener.in Data Scraper v2.0 - Enhanced with Date Extraction")
        self.root.geometry("1000x750")
        self.root.configure(bg='#f0f0f0')
        
        # Initialize variables
        self.scraper = None
        self.is_scraping = False
        self.progress_queue = queue.Queue()
        self.download_folder = str(Path.home() / "Downloads" / "ScreenerData")
        
        # Initialize stats variables
        self.stats_vars = {
            'files_downloaded': tk.StringVar(value='0'),
            'companies_processed': tk.StringVar(value='0'),
            'success_rate': tk.StringVar(value='0%')
        }
        
        # Create download folder if it doesn't exist
        os.makedirs(self.download_folder, exist_ok=True)
        
        self.setup_ui()
    
        self.setup_menu()
        
        # Start checking for progress updates
        self.check_progress_queue()
    
    def setup_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Change Download Folder", command=self.change_download_folder)
        file_menu.add_command(label="Open Download Folder", command=self.open_download_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Export Results", command=self.export_results)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Show Sample Filenames", command=self.show_sample_filenames)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Usage Guide", command=self.show_usage_guide)
        help_menu.add_command(label="Date Extraction Info", command=self.show_date_info)
    
    def setup_ui(self):
        """Setup the main user interface"""
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=tk.W + tk.E + tk.N + tk.S)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(9, weight=1)  # Changed from 8 to 9
        
        # Title
        title_label = ttk.Label(main_frame, text="Screener.in Data Scraper v2.0", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 5))
        
        # Subtitle
        subtitle_label = ttk.Label(main_frame, text="Enhanced with Date Extraction & Smart File Naming", 
                                  font=('Arial', 10, 'italic'), foreground='#666')
        subtitle_label.grid(row=1, column=0, columnspan=3, pady=(0, 15))
        
        # Company input section
        ttk.Label(main_frame, text="Company Symbols:", font=('Arial', 10, 'bold')).grid(
            row=2, column=0, sticky=tk.W, pady=(0, 5))
        
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=3, column=0, columnspan=3, sticky=tk.W + tk.E, pady=(0, 15))
        input_frame.columnconfigure(0, weight=1)
        
        self.company_entry = ttk.Entry(input_frame, font=('Arial', 10))
        self.company_entry.grid(row=0, column=0, sticky=tk.W + tk.E, padx=(0, 10))
        self.company_entry.insert(0, "RELIANCE, TCS, INFY")
        
        ttk.Button(input_frame, text="Add Company", 
                  command=self.add_company).grid(row=0, column=1)
        
        # Help text
        help_text = ttk.Label(main_frame, text="Enter company symbols separated by commas (e.g., RELIANCE, TCS, INFY)", 
                             font=('Arial', 8), foreground='gray')
        help_text.grid(row=4, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        
        # Document type selection
        doc_frame = ttk.LabelFrame(main_frame, text="Document Types to Download", padding="10")
        doc_frame.grid(row=5, column=0, columnspan=3, sticky=tk.W + tk.E, pady=(0, 15))
        
        self.doc_types = {
            'transcripts': tk.BooleanVar(value=True),
            'presentations': tk.BooleanVar(value=True),
            'notes': tk.BooleanVar(value=True),
            'annual_reports': tk.BooleanVar(value=True),
            'other_docs': tk.BooleanVar(value=False)
        }
        
        doc_labels = {
            'transcripts': 'Conference Call Transcripts',
            'presentations': 'Presentations (PPT/PDF)',
            'notes': 'Meeting Notes',
            'annual_reports': 'Annual Reports',
            'other_docs': 'Other Documents'
        }
        
        row = 0
        col = 0
        for key, var in self.doc_types.items():
            ttk.Checkbutton(doc_frame, text=doc_labels[key], 
                           variable=var).grid(row=row, column=col, sticky=tk.W, padx=10, pady=2)
            col += 1
            if col > 2:
                col = 0
                row += 1
        
        # File naming info
        naming_info = ttk.Label(doc_frame, 
                               text="✨ Files will be named with dates: SYMBOL_Date_Type.pdf (e.g., TCS_Q1-FY2024_transcript.pdf)",
                               font=('Arial', 8), foreground='#0078d4')
        naming_info.grid(row=row+1, column=0, columnspan=3, sticky=tk.W, pady=(10, 0))
        
        # Settings section
        settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding="10")
        settings_frame.grid(row=6, column=0, columnspan=3, sticky=tk.W + tk.E, pady=(0, 15))
        
        ttk.Label(settings_frame, text="Delay between requests (seconds):").grid(
            row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        self.delay_var = tk.StringVar(value="2")
        delay_spinbox = ttk.Spinbox(settings_frame, from_=1, to=10, width=5, 
                                   textvariable=self.delay_var)
        delay_spinbox.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(settings_frame, text="Download folder:").grid(
            row=1, column=0, sticky=tk.W, pady=(10, 0))
        
        self.folder_label = ttk.Label(settings_frame, text=self.download_folder, 
                                     foreground='blue', cursor='hand2')
        self.folder_label.grid(row=1, column=1, sticky=tk.W, pady=(10, 0))
        self.folder_label.bind("<Button-1>", lambda e: self.open_download_folder())
        
        # Date extraction options
        date_frame = ttk.LabelFrame(main_frame, text="Date Extraction Options", padding="10")
        date_frame.grid(row=7, column=0, columnspan=3, sticky=tk.W + tk.E, pady=(0, 15))
        
        self.sort_by_date = tk.BooleanVar(value=True)
        ttk.Checkbutton(date_frame, text="Sort documents by date (newest first)", 
                       variable=self.sort_by_date).grid(row=0, column=0, sticky=tk.W)
        
        self.extract_quarters = tk.BooleanVar(value=True)
        ttk.Checkbutton(date_frame, text="Extract quarter information (Q1, Q2, etc.)", 
                       variable=self.extract_quarters).grid(row=0, column=1, sticky=tk.W, padx=(20, 0))
         
            # Add stats section before the control buttons
        stats_frame = ttk.LabelFrame(main_frame, text="Statistics", padding="10")
        stats_frame.grid(row=7, column=0, columnspan=3, sticky=tk.W + tk.E, pady=(0, 15))

        # Stats display
        self.stats_vars = {
            'files_downloaded': tk.StringVar(value="0"),
            'companies_processed': tk.StringVar(value="0"),
            'success_rate': tk.StringVar(value="0%")
        }
        
        ttk.Label(stats_frame, text="Files Downloaded:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        ttk.Label(stats_frame, textvariable=self.stats_vars['files_downloaded'], 
                font=('Arial', 10, 'bold')).grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(stats_frame, text="Companies Processed:").grid(row=0, column=2, sticky=tk.W, padx=(20, 10))
        ttk.Label(stats_frame, textvariable=self.stats_vars['companies_processed'], 
                font=('Arial', 10, 'bold')).grid(row=0, column=3, sticky=tk.W)
        
        ttk.Label(stats_frame, text="Success Rate:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        ttk.Label(stats_frame, textvariable=self.stats_vars['success_rate'], 
                font=('Arial', 10, 'bold')).grid(row=1, column=1, sticky=tk.W)

        
        # Control buttons - Make sure this section is visible
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=8, column=0, columnspan=3, pady=15, sticky=tk.W + tk.E)
        
        self.start_button = ttk.Button(button_frame, text="Start Enhanced Scraping", 
                                      command=self.start_scraping)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(button_frame, text="Stop", 
                                     command=self.stop_scraping, state='disabled')
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_button = ttk.Button(button_frame, text="Clear Results", 
                                      command=self.clear_results)
        self.clear_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.preview_button = ttk.Button(button_frame, text="Preview Files", 
                                        command=self.preview_files)
        self.preview_button.pack(side=tk.LEFT)
        
        # Progress section
        progress_frame = ttk.LabelFrame(main_frame, text="Progress & Results", padding="10")
        progress_frame.grid(row=9, column=0, columnspan=3, sticky=tk.W + tk.E + tk.N + tk.S, pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        progress_frame.rowconfigure(1, weight=1)
        
        self.progress_var = tk.StringVar(value="Ready to start enhanced scraping...")
        self.progress_label = ttk.Label(progress_frame, textvariable=self.progress_var)
        self.progress_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.grid(row=0, column=1, sticky=tk.E, padx=(10, 0))
        
        # Results area with tabs
        notebook = ttk.Notebook(progress_frame)
        notebook.grid(row=1, column=0, columnspan=2, sticky=tk.W + tk.E + tk.N + tk.S, pady=(10, 0))
        
        # Main results tab
        results_frame = ttk.Frame(notebook)
        notebook.add(results_frame, text="Scraping Log")
        
        self.results_text = scrolledtext.ScrolledText(results_frame, height=15, width=90)
        self.results_text.pack(fill=tk.BOTH, expand=True)
        
        # File preview tab
        preview_frame = ttk.Frame(notebook)
        notebook.add(preview_frame, text="File Preview")
        
        self.preview_text = scrolledtext.ScrolledText(preview_frame, height=15, width=90)
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_var = tk.StringVar(value=f"Download folder: {self.download_folder} | Enhanced date extraction enabled")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=1, column=0, sticky=tk.W + tk.E)
    
    def add_company(self):
        """Add company to the input field"""
        current = self.company_entry.get()
        if current and not current.endswith(", "):
            self.company_entry.insert(tk.END, ", ")
        self.company_entry.focus()
    
    def change_download_folder(self):
        """Change the download folder"""
        folder = filedialog.askdirectory(initialdir=self.download_folder)
        if folder:
            self.download_folder = folder
            self.folder_label.config(text=folder)
            self.status_var.set(f"Download folder: {folder} | Enhanced date extraction enabled")
    
    def open_download_folder(self):
        """Open the download folder in file explorer"""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(self.download_folder)
            elif os.name == 'posix':  # macOS and Linux
                os.system(f'open "{self.download_folder}"')
        except:
            messagebox.showwarning("Warning", "Could not open folder")
    
    def preview_files(self):
        """Preview what files would be downloaded without actually downloading"""
        companies = [c.strip().upper() for c in self.company_entry.get().split(',') if c.strip()]
        
        if not companies:
            messagebox.showwarning("Warning", "Please enter at least one company symbol")
            return
        
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(tk.END, "🔍 PREVIEW MODE - No files will be downloaded\n")
        self.preview_text.insert(tk.END, "=" * 60 + "\n\n")
        
        # Start preview in separate thread
        thread = threading.Thread(target=self.preview_worker, args=(companies,))
        thread.daemon = True
        thread.start()
    
    def preview_worker(self, companies):
        """Worker thread for previewing files"""
        try:
            scraper = EnhancedScreenerScraper(delay=1)  # Faster for preview
            
            for company in companies[:2]:  # Limit to 2 companies for preview
                self.preview_text.insert(tk.END, f"📊 PREVIEWING: {company}\n")
                self.preview_text.insert(tk.END, "-" * 40 + "\n")
                self.preview_text.see(tk.END)
                self.root.update()
                
                company_url = scraper.find_company_by_symbol(company)
                if not company_url:
                    self.preview_text.insert(tk.END, f"❌ Could not find {company}\n\n")
                    continue
                
                company_data = scraper.extract_concall_data(company_url)
                if not company_data:
                    self.preview_text.insert(tk.END, f"❌ No data found for {company}\n\n")
                    continue
                
                self.preview_text.insert(tk.END, f"Found {len(company_data.concalls)} documents:\n\n")
                
                for i, doc in enumerate(company_data.concalls[:10]):  # Show first 10
                    filename = self.generate_filename(company, doc, i)
                    date_info = doc.date or "No date extracted"
                    
                    self.preview_text.insert(tk.END, f"📄 {filename}\n")
                    self.preview_text.insert(tk.END, f"   📅 Date: {date_info}\n")
                    self.preview_text.insert(tk.END, f"   📝 Title: {doc.title[:50]}...\n")
                    self.preview_text.insert(tk.END, f"   🏷️  Type: {doc.doc_type}\n\n")
                    
                    self.preview_text.see(tk.END)
                    self.root.update()
                
                if len(company_data.concalls) > 10:
                    self.preview_text.insert(tk.END, f"... and {len(company_data.concalls) - 10} more documents\n\n")
                
                self.preview_text.insert(tk.END, "-" * 60 + "\n\n")
                
        except Exception as e:
            self.preview_text.insert(tk.END, f"❌ Preview error: {str(e)}\n")
    
    def start_scraping(self):
        """Start the enhanced scraping process"""
        companies = [c.strip().upper() for c in self.company_entry.get().split(',') if c.strip()]
        
        if not companies:
            messagebox.showwarning("Warning", "Please enter at least one company symbol")
            return
        
        if not any(self.doc_types.values()):
            messagebox.showwarning("Warning", "Please select at least one document type")
            return
        
        self.is_scraping = True
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.progress_bar.start()
        
        # Clear previous results
        self.results_text.delete(1.0, tk.END)
        
        # Start scraping in separate thread
        thread = threading.Thread(target=self.enhanced_scraping_worker, args=(companies,))
        thread.daemon = True
        thread.start()
    
    def stop_scraping(self):
        """Stop the scraping process"""
        self.is_scraping = False
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.progress_bar.stop()
        self.progress_var.set("Stopping...")

    # Update the enhanced_scraping_worker method to update stats
    def enhanced_scraping_worker(self, companies):
        """Enhanced worker thread for scraping with date extraction"""
        try:
            delay = int(self.delay_var.get())
            scraper = EnhancedScreenerScraper(delay=delay)
            
            self.progress_queue.put(("status", "Initializing enhanced scraper..."))
            self.progress_queue.put(("result", "🚀 ENHANCED SCRAPER v2.0 - Date Extraction Enabled"))
            self.progress_queue.put(("result", "=" * 70))
            
            total_companies = len(companies)
            results = {}
            total_downloaded = 0
            companies_processed = 0
            
            # Update initial stats
            self.progress_queue.put(("stats", {
                'files_downloaded': total_downloaded,
                'companies_processed': companies_processed,
                'success_rate': 0
            }))
            
            for i, company in enumerate(companies, 1):
                if not self.is_scraping:
                    break
                
                self.progress_queue.put(("status", f"Processing {company} ({i}/{total_companies})"))
                self.progress_queue.put(("result", f"\n{'🏢 ' + company + ' ANALYSIS':<50}"))
                self.progress_queue.put(("result", f"{'='*70}"))
                
                try:
                    # Find company
                    company_url = scraper.find_company_by_symbol(company)
                    if not company_url:
                        self.progress_queue.put(("result", f"❌ Could not find company page for {company}"))
                        companies_processed += 1
                        continue
                    
                    self.progress_queue.put(("result", f"✅ Found: {company_url}"))
                    
                    # Extract data with enhanced date parsing
                    company_data = scraper.extract_concall_data(company_url)
                    if not company_data:
                        self.progress_queue.put(("result", f"❌ Could not extract data for {company}"))
                        companies_processed += 1
                        continue
                    
                    results[company] = company_data
                    
                    self.progress_queue.put(("result", f"🏭 Company: {company_data.company_name}"))
                    self.progress_queue.put(("result", f"📊 Found {len(company_data.concalls)} documents"))
                    
                    # Download documents
                    download_dir = os.path.join(self.download_folder, company)
                    downloaded_count = 0
                    
                    concalls = company_data.concalls if company_data.concalls is not None else []
                    annual_reports = company_data.annual_reports if company_data.annual_reports is not None else []
                    
                    # Download concall documents
                    for j, concall in enumerate(concalls[:5]):  # Limit to 5 concalls
                        if not self.is_scraping:
                            break
                        
                        filename = self.generate_filename(company, concall, j + 1)
                        self.progress_queue.put(("progress", f"📥 Downloading: {filename}"))
                        
                        if scraper.download_document(concall.url, filename, download_dir):
                            downloaded_count += 1
                            total_downloaded += 1
                            self.progress_queue.put(("result", f"✅ Downloaded: {filename}"))
                            
                            # Update stats after each download
                            success_rate = round((total_downloaded / max(1, i * 8)) * 100, 1)
                            self.progress_queue.put(("stats", {
                                'files_downloaded': total_downloaded,
                                'companies_processed': companies_processed,
                                'success_rate': success_rate
                            }))
                        else:
                            self.progress_queue.put(("result", f"❌ Failed to download: {filename}"))
                    
                    # Download annual reports
                    for j, report in enumerate(annual_reports[:3]):  # Limit to 3 annual reports
                        if not self.is_scraping:
                            break
                        
                        if self.doc_types['annual_reports'].get():
                            class SimpleDoc:
                                def __init__(self, **kwargs):
                                    for key, value in kwargs.items():
                                        setattr(self, key, value)
                            
                            temp_doc = SimpleDoc(
                                title=report.get('title', f'Annual Report {j+1}'),
                                url=report['url'],
                                doc_type='annual_report',
                                date=report.get('date', f'annual-report-{j+1}')
                            )
                            
                            filename = self.generate_filename(company, temp_doc, j + 100)
                            self.progress_queue.put(("progress", f"📥 Downloading: {filename}"))
                            
                            if scraper.download_document(report['url'], filename, download_dir):
                                downloaded_count += 1
                                total_downloaded += 1
                                self.progress_queue.put(("result", f"✅ Downloaded: {filename}"))
                                
                                # Update stats after each download
                                success_rate = round((total_downloaded / max(1, i * 8)) * 100, 1)
                                self.progress_queue.put(("stats", {
                                    'files_downloaded': total_downloaded,
                                    'companies_processed': companies_processed,
                                    'success_rate': success_rate
                                }))
                            else:
                                self.progress_queue.put(("result", f"❌ Failed to download: {filename}"))
                    
                    companies_processed += 1
                    self.progress_queue.put(("result", f"📊 Downloaded {downloaded_count} files for {company}"))
                    
                    # Update stats after each company
                    success_rate = round((total_downloaded / max(1, companies_processed * 8)) * 100, 1)
                    self.progress_queue.put(("stats", {
                        'files_downloaded': total_downloaded,
                        'companies_processed': companies_processed,
                        'success_rate': success_rate
                    }))
                    
                except Exception as e:
                    self.progress_queue.put(("result", f"❌ Error processing {company}: {str(e)}"))
                    companies_processed += 1
            
            # Final stats update
            final_success_rate = round((total_downloaded / max(1, companies_processed * 8)) * 100, 1)
            self.progress_queue.put(("stats", {
                'files_downloaded': total_downloaded,
                'companies_processed': companies_processed,
                'success_rate': final_success_rate
            }))
            
            self.progress_queue.put(("status", f"✅ Enhanced scraping completed! Downloaded {total_downloaded} files"))
            self.progress_queue.put(("result", f"\n📊 FINAL SUMMARY"))
            self.progress_queue.put(("result", f"Companies processed: {companies_processed}"))
            self.progress_queue.put(("result", f"Total files downloaded: {total_downloaded}"))
            self.progress_queue.put(("result", f"Success rate: {final_success_rate}%"))
            
        except Exception as e:
            self.progress_queue.put(("result", f"❌ Unexpected error: {str(e)}"))
        finally:
            self.progress_queue.put(("done", None))

    # Update the check_progress_queue method to handle stats
    def check_progress_queue(self):
        """Check for progress updates from worker thread"""
        try:
            while True:
                msg_type, data = self.progress_queue.get_nowait()
                
                if msg_type == "status":
                    self.progress_var.set(data)
                elif msg_type == "result":
                    self.results_text.insert(tk.END, data + "\n")
                    self.results_text.see(tk.END)
                elif msg_type == "stats":
                    # Update stats display
                    self.stats_vars['files_downloaded'].set(str(data['files_downloaded']))
                    self.stats_vars['companies_processed'].set(str(data['companies_processed']))
                    self.stats_vars['success_rate'].set(f"{data['success_rate']}%")
                elif msg_type == "done":
                    self.start_button.config(state='normal')
                    self.stop_button.config(state='disabled')
                    self.progress_bar.stop()
                    self.is_scraping = False
                    break
                    
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.check_progress_queue)

    def clear_results(self):
        """Clear the results area"""
        self.results_text.delete(1.0, tk.END)
        self.preview_text.delete(1.0, tk.END)
        self.progress_var.set("Ready to start enhanced scraping...")
    
    def export_results(self):
        """Export results to file"""
        content = self.results_text.get(1.0, tk.END)
        if not content.strip():
            messagebox.showwarning("Warning", "No results to export")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialdir=self.download_folder
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("Success", f"Results exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {str(e)}")
    
    def generate_filename(self, company, doc, index):
        """Generate filename for document"""
        doc_type = getattr(doc, 'doc_type', 'document')
        date_info = getattr(doc, 'date', f'doc-{index+1}')
        return f"{company}_{date_info}_{doc_type}.pdf"
    
    def show_sample_filenames(self):
        """Show sample filename patterns"""
        sample_window = tk.Toplevel(self.root)
        sample_window.title("Sample Filename Patterns")
        sample_window.geometry("600x400")
        
        text_widget = scrolledtext.ScrolledText(sample_window, wrap=tk.WORD, padx=10, pady=10)
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        samples = """Enhanced File Naming Examples:

📅 DATE-BASED NAMING:
✓ TCS_Q1-FY2024_transcript.pdf
✓ RELIANCE_Mar-2024_presentation.pdf
✓ INFY_Q3-FY2023_notes.pdf
✓ HDFCBANK_Feb-2024_concall.pdf

📊 QUARTER EXTRACTION:
✓ TCS_Q1-FY2024_transcript.pdf      (Quarter 1, FY 2024)
✓ WIPRO_Q4-FY2023_presentation.pdf  (Quarter 4, FY 2023)

📅 MONTH EXTRACTION:
✓ TCS_Jan-2024_transcript.pdf       (January 2024)
✓ INFY_Dec-2023_presentation.pdf    (December 2023)

🏷️ DOCUMENT TYPES:
✓ transcript - Conference call transcripts
✓ presentation - Investor presentations  
✓ notes - Meeting notes and summaries
✓ concall - General conference call documents
✓ annual_report - Annual/quarterly reports

📂 FOLDER ORGANIZATION:
Downloads/ScreenerData/
├── TCS/
│   ├── TCS_Q1-FY2024_transcript.pdf
│   ├── TCS_Q2-FY2024_presentation.pdf
│   └── TCS_Mar-2024_notes.pdf
└── RELIANCE/
    ├── RELIANCE_Q4-FY2023_transcript.pdf
    └── RELIANCE_Apr-2024_presentation.pdf

🔍 DATE EXTRACTION SUPPORTS:
• DD/MM/YYYY, MM/DD/YYYY formats
• Month names (Jan, February, etc.)
• Quarter patterns (Q1, Q2, Q3, Q4)
• Financial years (FY2024, FY 2023)
• Year-only patterns (2024, 2023)

💡 FILES WITHOUT DATES:
If no date is found, files are named:
✓ TCS_doc-1_transcript.pdf
✓ TCS_doc-2_presentation.pdf"""
        
        text_widget.insert(1.0, samples)
        text_widget.config(state=tk.DISABLED)
    
    def show_about(self):
        """Show about dialog"""
        about_text = """Screener.in Data Scraper v2.0 Enhanced

🚀 NEW FEATURES:
• Smart date extraction from document titles
• Quarter-aware file naming (Q1, Q2, Q3, Q4)
• Chronological file organization
• Enhanced document type detection
• File preview functionality

📊 EXTRACTION CAPABILITIES:
• Conference call transcripts with dates
• Presentations sorted chronologically  
• Annual reports with fiscal year info
• Meeting notes with time stamps

🎯 INTELLIGENT NAMING:
Files are automatically named with:
• Company symbol
• Extracted date/quarter
• Document type
• Proper file extension

Created for educational and research purposes.
Please use responsibly and respect server resources."""
        
        messagebox.showinfo("About Enhanced Scraper", about_text)
    
    def show_date_info(self):
        """Show date extraction information"""
        date_window = tk.Toplevel(self.root)
        date_window.title("Date Extraction Information")
        date_window.geometry("700x500")
        
        text_widget = scrolledtext.ScrolledText(date_window, wrap=tk.WORD, padx=10, pady=10)
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        date_info = """📅 DATE EXTRACTION CAPABILITIES

The enhanced scraper can extract dates from various formats:

🔢 NUMERIC FORMATS:
• 15/03/2024, 03/15/2024
• 15-03-2024, 03-15-2024
• 2024/03/15

📝 TEXT FORMATS:
• 15 March 2024, March 15 2024
• 15 Mar 2024, Mar 15, 2024
• March 2024, Mar 2024

📊 QUARTER FORMATS:
• Q1 FY2024, Q1 FY 2024
• Quarter 1 2024, 1Q 2024
• FY2024 Q1, FY 2024 Q1

📅 YEAR FORMATS:
• FY2024, FY 2024
• 2024 Annual
• Annual 2024

🎯 EXTRACTION PROCESS:

1. Document Title Analysis:
   The scraper examines each document title for date patterns

2. Context Analysis:
   If no date in title, checks surrounding HTML elements

3. Pattern Matching:
   Uses 15+ different regex patterns to catch various formats

4. Date Validation:
   Ensures extracted dates are valid (proper months, days)

5. Chronological Sorting:
   Documents are sorted by date (newest first)

📂 FILE ORGANIZATION:

Documents with dates:     SYMBOL_Date_Type.pdf
Documents with quarters:  SYMBOL_Q1-FY2024_Type.pdf  
Documents without dates:  SYMBOL_doc-1_Type.pdf

🔍 EXAMPLES OF EXTRACTED PATTERNS:

From: "Q1 FY2024 Earnings Call Transcript"
→ Extracts: Q1 FY2024
→ Filename: TCS_Q1-FY2024_transcript.pdf

From: "Investor Presentation March 2024"  
→ Extracts: Mar-2024
→ Filename: TCS_Mar-2024_presentation.pdf

From: "Annual Report 2023-24"
→ Extracts: FY2024
→ Filename: TCS_FY2024_annual_report.pdf

💡 TIPS FOR BEST RESULTS:

• Documents with standard naming get better date extraction
• Quarterly results typically have the most consistent patterns
• Annual reports usually include fiscal year information
• Some older documents may not have extractable dates"""
        
        text_widget.insert(1.0, date_info)
        text_widget.config(state=tk.DISABLED)
    
    def show_usage_guide(self):
        """Show enhanced usage guide"""
        guide_text = """📚 ENHANCED USAGE GUIDE

🚀 NEW FEATURES IN v2.0:

1. Smart Date Extraction:
   • Automatically finds dates in document titles
   • Supports quarters, months, and years
   • Creates chronologically organized file names

2. Enhanced File Naming:
   • SYMBOL_Date_Type.pdf format
   • Quarter-aware naming (Q1-FY2024)
   • Month-based naming (Mar-2024)

3. Preview Functionality:
   • See what files will be downloaded
   • Check date extraction accuracy
   • Preview filenames before downloading

📋 STEP-BY-STEP USAGE:

1. Enter Company Symbols:
   • Use exact symbols from Screener.in
   • Separate multiple companies with commas
   • Example: RELIANCE, TCS, INFY, HDFCBANK

2. Select Document Types:
   • Choose specific types you need
   • All types are date-organized automatically

3. Preview (Optional):
   • Click "Preview Files" to see what will be downloaded
   • Check date extraction results
   • Verify filename patterns

4. Configure Settings:
   • Set appropriate delay (2-3 seconds recommended)
   • Choose download folder location

5. Start Enhanced Scraping:
   • Monitor real-time progress
   • See date extraction in action
   • Files are automatically organized

📊 RESULTS INTERPRETATION:

✅ Date extracted for X/Y documents
This shows how many documents had extractable dates

📄 Filename examples in progress log
Shows the actual filenames being created

📅 Date patterns found
Displays quarter/month/year information extracted

🎯 PRO TIPS:

• Large companies have more documents with dates
• Quarterly results have the best date patterns  
• Preview first to understand what's available
• Check the download folder regularly during scraping

📂 FILE ORGANIZATION:

Downloads are organized by:
1. Company (separate folders)
2. Date (chronological naming)
3. Type (transcript, presentation, etc.)

This makes it easy to find specific documents later!"""
        
        # Create a new window for the guide
        guide_window = tk.Toplevel(self.root)
        guide_window.title("Enhanced Usage Guide")
        guide_window.geometry("600x700")
        
        text_widget = scrolledtext.ScrolledText(guide_window, wrap=tk.WORD, padx=10, pady=10)
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(1.0, guide_text)
        text_widget.config(state=tk.DISABLED)

def main():
    """Main function to run the enhanced GUI"""
    root = tk.Tk()
    
    # Set style
    style = ttk.Style()
    style.theme_use('clam')
    
    # Configure custom styles
    style.configure('Accent.TButton', foreground='white', background='#0078d4')
    
    app = EnhancedScreenerGUI(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\nApplication closed by user")

if __name__ == "__main__":
    main()