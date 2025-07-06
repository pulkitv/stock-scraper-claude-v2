# Stock Scraper - Enhanced Screener.in Document Downloader

## Overview
An enhanced Python application for scraping financial documents from Screener.in with both GUI and Web interfaces.

## Features
- ✅ **Desktop GUI Interface** with Tkinter
- ✅ **Web Interface** with Flask (NEW!)
- ✅ **Real-time Progress Updates** via WebSockets
- ✅ **File Management** - List, download, and clear files
- ✅ **Smart Date Extraction** from document titles
- ✅ **Batch Processing** for multiple companies
- ✅ **Document Type Selection** (transcripts, presentations, annual reports)
- ✅ **Responsive Design** - Works on desktop and mobile

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/pulkitv/stock-scraper.git
   cd stock-scraper
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv stock-scraper-env
   source stock-scraper-env/bin/activate  # On Windows: stock-scraper-env\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Web Interface (Recommended)
```bash
python app.py
```
Then open your browser and go to: `http://localhost:5000`

### Desktop GUI
```bash
python screener_gui.py
```

## Web Interface Features

- **Modern Dashboard** - Clean, responsive design
- **Real-time Updates** - Live progress via WebSockets
- **File Management** - View, download, and manage files
- **Statistics** - Download counts and success rates
- **Mobile Friendly** - Works on all devices

## API Endpoints

- `GET /` - Main web interface
- `POST /api/start-scraping` - Start scraping process
- `POST /api/stop-scraping` - Stop scraping process
- `GET /api/status` - Get scraping status
- `GET /api/files` - List downloaded files
- `POST /api/files/clear` - Clear all files
- `GET /downloads/<path>` - Download specific file

## File Structure
```
stock-scraper/
├── app.py                  # Flask web application
├── screener_gui.py         # Desktop GUI application
├── screener_scraper.py     # Core scraping logic
├── templates/
│   └── index.html         # Web interface template
├── downloads/             # Downloaded files directory
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Sample Output
Files are saved with smart naming:
- `RELIANCE_FY2024_annual_report.pdf`
- `TCS_Q1-FY2024_transcript.pdf`
- `INFY_Mar-2024_presentation.pdf`

## Technologies Used
- **Backend**: Python, Flask, Flask-SocketIO
- **Frontend**: HTML5, CSS3, JavaScript
- **Web Scraping**: BeautifulSoup4, Requests
- **GUI**: Tkinter
- **Real-time**: WebSockets

## License
MIT License

## Contributing
Pull requests are welcome. For major changes, please open an issue first.

## Deployment

### Railway (Recommended)
1. Fork/clone this repository
2. Go to [railway.app](https://railway.app)
3. Sign up with GitHub
4. Click "New Project" → "Deploy from GitHub repo"
5. Select your `stock-scraper` repository
6. Railway will automatically detect and deploy your app
7. Your app will be live at: `https://your-app-name.railway.app`

### Local Development
```bash
python app.py
```
Then open: `http://localhost:5000`

### Environment Variables
- `PORT` - Port number (automatically set by Railway)
- `DEBUG` - Set to `False` for production (optional)

## Live Demo
🚀 **[Try the live demo](https://your-app-name.railway.app)**

## Screenshots

### Web Interface
![Web Interface](screenshot-web.png)

### Desktop GUI
![Desktop GUI](screenshot-gui.png)
