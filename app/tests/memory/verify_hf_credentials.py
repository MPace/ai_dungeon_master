#!/usr/bin/env python3
"""
Simple script to verify Hugging Face API credentials

Usage:
    python3 verify_hf_credentials.py [API_URL] [API_TOKEN]

If no arguments are provided, it will use HF_API_URL and HF_API_TOKEN 
environment variables.
"""
import os
import sys
import requests
import json

def verify_credentials(api_url, api_token):
    """Verify Hugging Face API credentials by making a test request"""
    print(f"Verifying Hugging Face API credentials:")
    print(f"API URL: {api_url}")
    print(f"API Token: {api_token[:4]}...{api_token[-4:] if len(api_token) > 8 else ''}")
    
    # Try a simple API request to verify the token
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    try:
        # First try a simple text to test the connection
        test_text = "Hello, this is a test."
        test_payload = {
            "inputs": test_text,
            "parameters": {
                "max_length": 50,
                "min_length": 10
            }
        }
        
        print(f"\nSending test request to: {api_url}")
        print(f"Test payload: {json.dumps(test_payload, indent=2)}")
        
        response = requests.post(api_url, headers=headers, json=test_payload, timeout=30)
        
        print(f"Response status code: {response.status_code}")
        print(f"Response content type: {response.headers.get('Content-Type', 'unknown')}")
        
        if response.status_code == 200:
            print(f"\n✅ SUCCESS! API credentials are valid.")
            print(f"\nResponse data:")
            print(json.dumps(response.json(), indent=2))
            return True
        else:
            print(f"\n❌ ERROR: API request failed with status {response.status_code}")
            print(f"\nResponse text:")
            print(response.text)
            
            # Check for common error conditions
            if response.status_code == 401:
                print("\nThis looks like an authentication error. Your API token may be invalid.")
            elif response.status_code == 404:
                print("\nThis looks like a 404 error. The API URL may be incorrect or the model doesn't exist.")
            elif response.status_code == 503:
                print("\nThis looks like a service unavailable error. The model might be loading or the server is busy.")
            
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ ERROR: Request failed: {e}")
        
        # More detailed error information
        if isinstance(e, requests.exceptions.ConnectionError):
            print("\nThis looks like a connection error. Check your internet connection or API URL.")
        elif isinstance(e, requests.exceptions.Timeout):
            print("\nThe request timed out. The service might be overloaded.")
        
        return False
    except json.JSONDecodeError:
        print(f"\n❌ ERROR: Could not parse response as JSON.")
        print(f"Response text: {response.text[:500]}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: Unexpected error: {e}")
        return False

def main():
    """Main entry point"""
    # Get API credentials from command line args or environment variables
    if len(sys.argv) >= 3:
        api_url = sys.argv[1]
        api_token = sys.argv[2]
    else:
        api_url = os.environ.get("HF_API_URL")
        api_token = os.environ.get("HF_API_TOKEN")
    
    if not api_url:
        print("ERROR: No API URL provided. Please provide it as an argument or set the HF_API_URL environment variable.")
        print(f"Example: HF_API_URL=https://api-inference.huggingface.co/models/facebook/bart-large-cnn")
        return 1
        
    if not api_token:
        print("ERROR: No API token provided. Please provide it as an argument or set the HF_API_TOKEN environment variable.")
        print("You can get a token from https://huggingface.co/settings/tokens")
        return 1
    
    # Verify credentials
    result = verify_credentials(api_url, api_token)
    
    # Return appropriate exit code
    return 0 if result else 1

if __name__ == "__main__":
    sys.exit(main())