#!/usr/bin/env python3
"""
HTTP MCP Server for Stock Scraper Integration with Claude Desktop
"""

import asyncio
import json
import logging
import sys
import os
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
import uvicorn

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp.server import Server
from mcp.types import Tool, TextContent
from screener_scraper import EnhancedScreenerScraper
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Stock Scraper MCP Server")

# Create MCP server instance
server = Server("stock-scraper")

# Initialize scraper
try:
    scraper = EnhancedScreenerScraper(delay=2)
    logger.info("Scraper initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize scraper: {e}")
    sys.exit(1)

@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools"""
    return [
        Tool(
            name="find_company_by_symbol",
            description="Find a company by its stock symbol",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Company stock symbol (e.g., RELIANCE, INFY)"
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="scrape_company_data",
            description="Get comprehensive company data including documents and PDFs",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Company stock symbol (e.g., RELIANCE, INFY)"
                    },
                    "download_docs": {
                        "type": "boolean",
                        "description": "Whether to download documents",
                        "default": False
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="extract_concall_data",
            description="Extract concall data from a company URL",
            inputSchema={
                "type": "object",
                "properties": {
                    "company_url": {
                        "type": "string",
                        "description": "URL of the company on screener.in"
                    }
                },
                "required": ["company_url"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls"""
    logger.info(f"Tool called: {name} with arguments: {arguments}")
    
    try:
        if name == "find_company_by_symbol":
            return await find_company_by_symbol_handler(arguments)
        elif name == "scrape_company_data":
            return await scrape_company_data_handler(arguments)
        elif name == "extract_concall_data":
            return await extract_concall_data_handler(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        logger.error(f"Error in tool {name}: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def find_company_by_symbol_handler(arguments: Dict[str, Any]) -> List[TextContent]:
    """Find a company by symbol"""
    symbol = arguments.get("symbol", "").upper()
    logger.info(f"Finding company by symbol: {symbol}")
    
    try:
        result = scraper.find_company_by_symbol(symbol)
        
        if not result:
            return [TextContent(
                type="text",
                text=f"No company found for symbol: {symbol}"
            )]
        
        response = f"Company found for symbol '{symbol}':\n\n"
        response += f"Company URL: {result}\n"
        
        return [TextContent(type="text", text=response)]
    except Exception as e:
        logger.error(f"Error finding company by symbol: {e}")
        return [TextContent(type="text", text=f"Error finding company by symbol: {str(e)}")]

async def scrape_company_data_handler(arguments: Dict[str, Any]) -> List[TextContent]:
    """Scrape company data"""
    symbol = arguments.get("symbol", "").upper()
    download_docs = arguments.get("download_docs", False)
    logger.info(f"Scraping company data for symbol: {symbol}, download_docs: {download_docs}")
    
    try:
        result = scraper.scrape_company_data(symbol, download_docs=download_docs)
        
        if not result:
            return [TextContent(
                type="text",
                text=f"No data found for symbol: {symbol}"
            )]
        
        # Format the response based on the result structure
        response = f"Company data for symbol '{symbol}':\n\n"
        
        if isinstance(result, dict):
            # If result is a dictionary, format it nicely
            for key, value in result.items():
                if isinstance(value, list):
                    response += f"## {key.replace('_', ' ').title()} ({len(value)} items)\n"
                    for i, item in enumerate(value, 1):
                        if isinstance(item, dict):
                            response += f"{i}. {item.get('title', item.get('name', 'Unknown'))}\n"
                            if item.get('date'):
                                response += f"   Date: {item['date']}\n"
                            if item.get('url'):
                                response += f"   URL: {item['url']}\n"
                        else:
                            response += f"{i}. {str(item)}\n"
                    response += "\n"
                else:
                    response += f"**{key.replace('_', ' ').title()}**: {value}\n"
        else:
            response += f"Result: {str(result)}\n"
        
        return [TextContent(type="text", text=response)]
    except Exception as e:
        logger.error(f"Error scraping company data: {e}")
        return [TextContent(type="text", text=f"Error scraping company data: {str(e)}")]

async def extract_concall_data_handler(arguments: Dict[str, Any]) -> List[TextContent]:
    """Extract concall data from company URL"""
    company_url = arguments.get("company_url", "")
    logger.info(f"Extracting concall data from URL: {company_url}")
    
    try:
        result = scraper.extract_concall_data(company_url)
        
        if not result:
            return [TextContent(
                type="text",
                text=f"No concall data found for URL: {company_url}"
            )]
        
        response = f"Concall data extracted from: {company_url}\n\n"
        
        if hasattr(result, '__dict__'):
            # If result is a dataclass or object with attributes
            for key, value in result.__dict__.items():
                if isinstance(value, list):
                    response += f"## {key.replace('_', ' ').title()} ({len(value)} items)\n"
                    for i, item in enumerate(value, 1):
                        if isinstance(item, dict):
                            response += f"{i}. {item.get('title', item.get('name', 'Unknown'))}\n"
                            if item.get('date'):
                                response += f"   Date: {item['date']}\n"
                            if item.get('url'):
                                response += f"   URL: {item['url']}\n"
                        else:
                            response += f"{i}. {str(item)}\n"
                    response += "\n"
                else:
                    response += f"**{key.replace('_', ' ').title()}**: {value}\n"
        else:
            response += f"Result: {str(result)}\n"
        
        return [TextContent(type="text", text=response)]
    except Exception as e:
        logger.error(f"Error extracting concall data: {e}")
        return [TextContent(type="text", text=f"Error extracting concall data: {str(e)}")]

# FastAPI endpoints for MCP over HTTP
@app.post("/mcp/tools/list")
async def list_tools_endpoint():
    """List available tools endpoint"""
    try:
        tools = await list_tools()
        return {"tools": [tool.model_dump() for tool in tools]}
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        return {"error": str(e)}

@app.post("/mcp/tools/call")
async def call_tool_endpoint(request: Request):
    """Call tool endpoint"""
    try:
        data = await request.json()
        name = data.get("name")
        arguments = data.get("arguments", {})
        
        result = await call_tool(name, arguments)
        return {"result": [content.model_dump() for content in result]}
    except Exception as e:
        logger.error(f"Error calling tool: {e}")
        return {"error": str(e)}

@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "server": "stock-scraper-mcp"}

@app.get("/health")
async def health():
    """Health endpoint"""
    return {"status": "ok"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)