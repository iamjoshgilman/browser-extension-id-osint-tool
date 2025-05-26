#!/usr/bin/env python3
"""
Health check script for Browser Extension OSINT Tool
"""
import requests
import sys
import os
from urllib.parse import urljoin

def check_backend(base_url, api_key=None):
    """Check if backend is healthy"""
    print("🔍 Checking backend health...")
    
    try:
        # Check health endpoint
        health_url = urljoin(base_url, '/api/health')
        response = requests.get(health_url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend is healthy")
            print(f"   Version: {data.get('version', 'unknown')}")
            print(f"   Database: {'Present' if data.get('database') else 'Missing'}")
        else:
            print(f"❌ Backend health check failed: HTTP {response.status_code}")
            return False
            
        # Test search endpoint
        print("\n🔍 Testing search endpoint...")
        search_url = urljoin(base_url, '/api/search')
        headers = {}
        if api_key:
            headers['X-API-Key'] = api_key
            
        test_data = {
            'extension_id': 'cjpalhdlnbpafiamejdnhcphjbkeiagm',
            'stores': ['chrome']
        }
        
        response = requests.post(search_url, json=test_data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Search endpoint working")
            print(f"   Results: {len(data.get('results', []))} found")
        elif response.status_code == 401:
            print(f"❌ Search endpoint requires API key")
            if not api_key:
                print("   Tip: Set API_KEY environment variable or pass it as argument")
            return False
        else:
            print(f"❌ Search endpoint failed: HTTP {response.status_code}")
            return False
            
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend")
        print("   Make sure the backend is running on", base_url)
        return False
    except Exception as e:
        print(f"❌ Error checking backend: {e}")
        return False

def check_frontend(base_url):
    """Check if frontend is accessible"""
    print("\n🔍 Checking frontend...")
    
    try:
        response = requests.get(base_url, timeout=5)
        
        if response.status_code == 200:
            if 'Browser Extension OSINT Tool' in response.text:
                print("✅ Frontend is accessible")
                return True
            else:
                print("⚠️  Frontend is accessible but content looks wrong")
                return True
        else:
            print(f"❌ Frontend returned HTTP {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to frontend")
        print("   Make sure the frontend is being served on", base_url)
        return False
    except Exception as e:
        print(f"❌ Error checking frontend: {e}")
        return False

def main():
    """Run health checks"""
    print("Browser Extension OSINT Tool - Health Check")
    print("==========================================\n")
    
    # Get configuration from environment or defaults
    backend_url = os.environ.get('BACKEND_URL', 'http://localhost:5000')
    frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost')
    api_key = os.environ.get('API_KEY', None)
    
    # Allow command line arguments
    if len(sys.argv) > 1:
        backend_url = sys.argv[1]
    if len(sys.argv) > 2:
        frontend_url = sys.argv[2]
    if len(sys.argv) > 3:
        api_key = sys.argv[3]
    
    print(f"Backend URL: {backend_url}")
    print(f"Frontend URL: {frontend_url}")
    print(f"API Key: {'Set' if api_key else 'Not set'}\n")
    
    backend_ok = check_backend(backend_url, api_key)
    frontend_ok = check_frontend(frontend_url)
    
    print("\n" + "="*50)
    if backend_ok and frontend_ok:
        print("✅ All systems operational!")
        sys.exit(0)
    else:
        print("❌ Some systems are not working properly")
        sys.exit(1)

if __name__ == "__main__":
    main()
