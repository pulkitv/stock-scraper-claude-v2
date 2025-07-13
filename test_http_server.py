import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    response = requests.get(f"{BASE_URL}/")
    print("Health check:", response.json())

def test_list_tools():
    response = requests.post(f"{BASE_URL}/mcp/tools/list")
    print("Tools list:", response.json())

def test_search_companies():
    data = {
        "name": "search_companies",
        "arguments": {"query": "Reliance"}
    }
    response = requests.post(f"{BASE_URL}/mcp/tools/call", json=data)
    print("Search companies:", response.json())

def test_get_documents():
    data = {
        "name": "get_company_documents",
        "arguments": {"company_name": "Reliance"}
    }
    response = requests.post(f"{BASE_URL}/mcp/tools/call", json=data)
    print("Get documents:", response.json())

if __name__ == "__main__":
    print("Testing HTTP MCP Server...")
    test_health()
    test_list_tools()
    test_search_companies()
    test_get_documents()