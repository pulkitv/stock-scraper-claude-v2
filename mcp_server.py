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
from mcp.server.sse import sse_server
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
            name="search_companies",
            description="Search for companies by name or symbol",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Company name or symbol to search for"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_company_documents",
            description="Get all available documents (PDFs) for a company",
            inputSchema={
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "Name of the company"
                    }
                },
                "required": ["company_name"]
            }
        ),
        Tool(
            name="get_company_pdfs",
            description="Get PDF URLs for a specific company",
            inputSchema={
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "Name of the company"
                    }
                },
                "required": ["company_name"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls"""
    logger.info(f"Tool called: {name} with arguments: {arguments}")
    
    try:
        if name == "search_companies":
            return await search_companies(arguments)
        elif name == "get_company_documents":
            return await get_company_documents(arguments)
        elif name == "get_company_pdfs":
            return await get_company_pdfs(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        logger.error(f"Error in tool {name}: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def search_companies(arguments: Dict[str, Any]) -> List[TextContent]:
    """Search for companies"""
    query = arguments.get("query", "")
    logger.info(f"Searching for companies with query: {query}")
    
    try:
        results = scraper.search_companies(query)
        
        if not results:
            return [TextContent(
                type="text",
                text=f"No companies found for query: {query}"
            )]
        
        response = f"Found {len(results)} companies for '{query}':\n\n"
        for i, company in enumerate(results, 1):
            response += f"{i}. {company.get('name', 'Unknown')} ({company.get('symbol', 'N/A')})\n"
            if company.get('url'):
                response += f"   URL: {company['url']}\n"
            response += "\n"
        
        return [TextContent(type="text", text=response)]
    except Exception as e:
        logger.error(f"Error searching companies: {e}")
        return [TextContent(type="text", text=f"Error searching companies: {str(e)}")]

async def get_company_documents(arguments: Dict[str, Any]) -> List[TextContent]:
    """Get company documents"""
    company_name = arguments.get("company_name", "")
    logger.info(f"Getting documents for company: {company_name}")
    
    try:
        search_results = scraper.search_companies(company_name)
        if not search_results:
            return [TextContent(
                type="text",
                text=f"Company '{company_name}' not found"
            )]
        
        company = search_results[0]
        symbol = company.get('symbol', '')
        
        company_data = scraper.get_company_data(symbol)
        if not company_data:
            return [TextContent(
                type="text",
                text=f"No data found for company '{company_name}'"
            )]
        
        response = f"Documents for {company_data.get('company_name', company_name)} ({symbol}):\n\n"
        total_docs = 0
        
        for doc_type in ['concalls', 'annual_reports', 'transcripts', 'presentations']:
            if doc_type in company_data and company_data[doc_type]:
                docs = company_data[doc_type]
                response += f"## {doc_type.replace('_', ' ').title()} ({len(docs)} documents)\n"
                for doc in docs:
                    response += f"- {doc.get('title', 'Unknown')} ({doc.get('date', 'Unknown date')})\n"
                    if doc.get('url'):
                        response += f"  URL: {doc['url']}\n"
                response += "\n"
                total_docs += len(docs)
        
        if total_docs == 0:
            response += "No documents found."
        else:
            response += f"Total documents: {total_docs}"
        
        return [TextContent(type="text", text=response)]
    except Exception as e:
        logger.error(f"Error getting documents: {e}")
        return [TextContent(type="text", text=f"Error getting documents: {str(e)}")]

async def get_company_pdfs(arguments: Dict[str, Any]) -> List[TextContent]:
    """Get PDF URLs for a company"""
    company_name = arguments.get("company_name", "")
    logger.info(f"Getting PDFs for company: {company_name}")
    
    try:
        search_results = scraper.search_companies(company_name)
        if not search_results:
            return [TextContent(
                type="text",
                text=f"Company '{company_name}' not found"
            )]
        
        company = search_results[0]
        symbol = company.get('symbol', '')
        
        company_data = scraper.get_company_data(symbol)
        if not company_data:
            return [TextContent(
                type="text",
                text=f"No data found for company '{company_name}'"
            )]
        
        pdf_urls = []
        for doc_type in ['concalls', 'annual_reports', 'transcripts', 'presentations']:
            if doc_type in company_data:
                for doc in company_data[doc_type]:
                    if 'url' in doc:
                        pdf_urls.append({
                            "type": doc_type,
                            "title": doc.get('title', 'Unknown'),
                            "url": doc['url'],
                            "date": doc.get('date', 'Unknown')
                        })
        
        if not pdf_urls:
            return [TextContent(
                type="text",
                text=f"No documents found for {company_name}"
            )]
        
        response = f"Documents for {company_data.get('company_name', company_name)}:\n\n"
        for pdf in pdf_urls:
            response += f"**{pdf['title']}** ({pdf['type']})\n"
            response += f"Date: {pdf['date']}\n"
            response += f"URL: {pdf['url']}\n\n"
        
        return [TextContent(type="text", text=response)]
    except Exception as e:
        logger.error(f"Error getting PDFs: {e}")
        return [TextContent(type="text", text=f"Error getting PDFs: {str(e)}")]

# Mount MCP server on FastAPI
@app.get("/sse")
async def handle_sse(request: Request):
    """Handle SSE connections for MCP"""
    return StreamingResponse(
        sse_server(server, request),
        media_type="text/event-stream"
    )

@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "server": "stock-scraper-mcp"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)