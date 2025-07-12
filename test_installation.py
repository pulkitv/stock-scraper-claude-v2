# test_installation.py
try:
    import fastapi
    import uvicorn
    import pydantic
    import requests
    from bs4 import BeautifulSoup
    print("✅ All required packages are installed!")
except ImportError as e:
    print(f"❌ Missing package: {e}")