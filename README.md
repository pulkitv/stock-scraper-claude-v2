# Stock Scraper - Enhanced Screener.in Document Downloader

## Overview
An enhanced Python application for scraping financial documents from Screener.in with a user-friendly GUI interface.

## Features
- ✅ GUI Interface with Tkinter
- ✅ Date extraction from document titles
- ✅ Smart file naming with dates and types
- ✅ Download concall transcripts and presentations
- ✅ Download annual reports (Financial Year documents)
- ✅ Batch processing for multiple companies
- ✅ Progress tracking and error handling

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/stock-scraper.git
   cd stock-scraper
   ```

2. **Install required packages:**
   ```bash
   pip install beautifulsoup4 requests
   ```

## Usage

1. **Run the GUI application:**
   ```bash
   python3 screener_gui.py
   ```

2. **Enter company symbols** (e.g., RELIANCE, TCS, INFY)

3. **Select document types** to download

4. **Choose download folder** and click "Start Enhanced Scraping"

## File Structure
```
stock-scraper/
├── screener_gui.py          # Main GUI application
├── screener_scraper.py      # Core scraping logic
├── README.md               # This file
└── downloads/              # Default download directory
```

## Sample Output
Files are saved with smart naming:
- `RELIANCE_FY2024_annual_report.pdf`
- `TCS_Q1-FY2024_transcript.pdf`
- `INFY_Mar-2024_presentation.pdf`

## Requirements
- Python 3.7+
- beautifulsoup4
- requests
- tkinter (usually comes with Python)

## License
MIT License

## Contributing
Pull requests are welcome. For major changes, please open an issue first.
