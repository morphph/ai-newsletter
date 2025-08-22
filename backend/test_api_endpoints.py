#!/usr/bin/env python3
"""
Test API endpoints to verify database schema alignment
"""

import requests
import json
from datetime import datetime, date, timedelta
from typing import Dict, List
import sys

# Base URL for the API (adjust if needed)
BASE_URL = "http://localhost:8000"  # Adjust port if different

class APITester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def test_endpoint(self, method: str, endpoint: str, params: Dict = None, 
                     data: Dict = None, expected_status: int = 200) -> bool:
        """Test a single endpoint"""
        url = f"{self.base_url}{endpoint}"
        test_name = f"{method} {endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, params=params)
            elif method == "POST":
                response = requests.post(url, json=data)
            elif method == "PUT":
                response = requests.put(url, json=data)
            elif method == "DELETE":
                response = requests.delete(url)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            success = response.status_code == expected_status
            
            result = {
                'test': test_name,
                'status': response.status_code,
                'expected': expected_status,
                'success': success,
                'response': response.json() if response.content else None
            }
            
            self.results.append(result)
            
            if success:
                self.passed += 1
                print(f"✅ {test_name}: {response.status_code}")
            else:
                self.failed += 1
                print(f"❌ {test_name}: {response.status_code} (expected {expected_status})")
                if response.content:
                    print(f"   Response: {response.text[:200]}")
            
            return success
            
        except requests.exceptions.ConnectionError:
            print(f"❌ {test_name}: Connection failed - Is the API running?")
            self.failed += 1
            self.results.append({
                'test': test_name,
                'error': 'Connection failed',
                'success': False
            })
            return False
        except Exception as e:
            print(f"❌ {test_name}: {str(e)}")
            self.failed += 1
            self.results.append({
                'test': test_name,
                'error': str(e),
                'success': False
            })
            return False
    
    def run_all_tests(self):
        """Run all API endpoint tests"""
        print("=" * 60)
        print("TESTING API ENDPOINTS")
        print("=" * 60)
        print(f"Base URL: {self.base_url}")
        print()
        
        # Test health check
        print("1. Testing Health Check:")
        self.test_endpoint("GET", "/api/monitoring/health")
        print()
        
        # Test sources endpoints
        print("2. Testing Sources Endpoints:")
        self.test_endpoint("GET", "/api/sources")
        self.test_endpoint("GET", "/api/sources/active")
        self.test_endpoint("GET", "/api/sources/by-type/website")
        self.test_endpoint("GET", "/api/sources/by-type/twitter")
        print()
        
        # Test articles endpoints
        print("3. Testing Articles Endpoints:")
        self.test_endpoint("GET", "/api/articles", params={"limit": 5})
        self.test_endpoint("GET", "/api/articles/today")
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        self.test_endpoint("GET", f"/api/articles/by-date/{yesterday}")
        print()
        
        # Test tweets endpoints
        print("4. Testing Tweets Endpoints:")
        self.test_endpoint("GET", "/api/tweets", params={"limit": 5})
        self.test_endpoint("GET", f"/api/tweets/by-date/{yesterday}")
        self.test_endpoint("GET", "/api/tweets/top-engagement", params={"days": 7, "limit": 5})
        print()
        
        # Test unified content endpoints
        print("5. Testing Unified Content Endpoints:")
        self.test_endpoint("GET", "/api/content/unified", params={"limit": 5})
        self.test_endpoint("GET", "/api/content/feed/today")
        self.test_endpoint("GET", "/api/content/feed/trending", params={"days": 7, "limit": 5})
        self.test_endpoint("GET", "/api/content/stats/daily", params={"days": 3})
        print()
        
        # Print summary
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Total tests: {self.passed + self.failed}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        
        if self.failed == 0:
            print("\n✅ All tests passed! API is working correctly with the database schema.")
        else:
            print(f"\n⚠️  {self.failed} tests failed. Please review the errors above.")
        
        return self.failed == 0
    
    def save_results(self, filename: str = "api_test_results.json"):
        """Save test results to a JSON file"""
        with open(filename, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'base_url': self.base_url,
                'summary': {
                    'total': self.passed + self.failed,
                    'passed': self.passed,
                    'failed': self.failed
                },
                'results': self.results
            }, f, indent=2, default=str)
        
        print(f"\nTest results saved to: {filename}")

def check_api_running(base_url: str) -> bool:
    """Check if the API is running"""
    try:
        # Try health endpoint first, then docs endpoint
        response = requests.get(f"{base_url}/api/monitoring/health", timeout=2)
        if response.status_code == 200:
            return True
        # Try docs endpoint as fallback
        response = requests.get(f"{base_url}/docs", timeout=2)
        return response.status_code == 200
    except:
        return False

def main():
    """Main execution"""
    # Check if API is running
    if not check_api_running(BASE_URL):
        print("⚠️  API is not running!")
        print("\nTo start the API, run:")
        print("cd /Users/bytedance/Desktop/test_ainews_0804/backend")
        print("python run.py")
        print("\nThen run this test script again.")
        return 1
    
    # Run tests
    tester = APITester()
    success = tester.run_all_tests()
    
    # Save results
    tester.save_results("/Users/bytedance/Desktop/test_ainews_0804/api_test_results.json")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())