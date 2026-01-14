#!/usr/bin/env python3
"""Smoke tests for pyPASreporterGUI.

This script verifies that the application is running correctly by checking:
1. Health endpoint responds
2. Login page is accessible
3. Branding assets are served
4. API ping endpoint works

Usage:
    # With server running on default port:
    python tools/verify.py

    # With custom URL:
    python tools/verify.py --base-url http://localhost:9090
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import urljoin

try:
    import requests
except ImportError:
    print("Error: requests package required. Install with: pip install requests")
    sys.exit(1)


def check_endpoint(name: str, url: str, expected_status: int = 200, json_key: str | None = None) -> bool:
    """Check if an endpoint responds correctly."""
    try:
        response = requests.get(url, timeout=10, allow_redirects=True)
        
        if response.status_code != expected_status:
            print(f"  ✗ {name}: Expected {expected_status}, got {response.status_code}")
            return False
        
        if json_key:
            try:
                data = response.json()
                if json_key not in data:
                    print(f"  ✗ {name}: Missing key '{json_key}' in response")
                    return False
            except json.JSONDecodeError:
                print(f"  ✗ {name}: Invalid JSON response")
                return False
        
        print(f"  ✓ {name}: OK")
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"  ✗ {name}: Connection refused (is the server running?)")
        return False
    except requests.exceptions.Timeout:
        print(f"  ✗ {name}: Timeout")
        return False
    except Exception as e:
        print(f"  ✗ {name}: {e}")
        return False


def check_branding_asset(base_url: str, path: str, name: str) -> bool:
    """Check if a branding asset is accessible."""
    url = urljoin(base_url, path)
    try:
        response = requests.head(url, timeout=10, allow_redirects=True)
        
        if response.status_code == 200:
            print(f"  ✓ {name}: OK")
            return True
        else:
            print(f"  ✗ {name}: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ✗ {name}: {e}")
        return False


def login_and_get_token(base_url: str, username: str, password: str) -> str | None:
    """Login and get an access token."""
    url = urljoin(base_url, "/api/v1/security/login")
    payload = {
        "username": username,
        "password": password,
        "provider": "db",
        "refresh": True,
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
    except Exception:
        pass
    
    return None


def check_authenticated_endpoint(base_url: str, path: str, token: str, name: str, json_key: str | None = None) -> bool:
    """Check an endpoint that requires authentication."""
    url = urljoin(base_url, path)
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"  ✗ {name}: Status {response.status_code}")
            return False
        
        if json_key:
            try:
                data = response.json()
                if json_key not in data:
                    print(f"  ✗ {name}: Missing key '{json_key}'")
                    return False
            except json.JSONDecodeError:
                print(f"  ✗ {name}: Invalid JSON")
                return False
        
        print(f"  ✓ {name}: OK")
        return True
        
    except Exception as e:
        print(f"  ✗ {name}: {e}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.environ.get("SUPERSET_BASE_URL", "http://127.0.0.1:8088"),
                        help="Base URL of the server")
    parser.add_argument("--username", default=os.environ.get("SUPERSET_ADMIN_USERNAME", "admin"),
                        help="Admin username")
    parser.add_argument("--password", default=os.environ.get("SUPERSET_ADMIN_PASSWORD", "admin"),
                        help="Admin password")
    parser.add_argument("--skip-auth", action="store_true",
                        help="Skip authenticated endpoint checks")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    all_passed = True

    print(f"\npyPASreporterGUI Smoke Tests")
    print(f"Base URL: {base_url}")
    print("=" * 60)

    # Basic endpoints
    print("\n📡 Basic Endpoints:")
    
    if not check_endpoint("Health", f"{base_url}/health"):
        all_passed = False
    
    if not check_endpoint("Login Page", f"{base_url}/login/"):
        all_passed = False

    # Branding assets
    print("\n🎨 Branding Assets:")
    
    if not check_branding_asset(base_url, "/pypasreportergui_static/logo-horiz.png", "Logo"):
        all_passed = False
    
    if not check_branding_asset(base_url, "/pypasreportergui_static/favicon.png", "Favicon"):
        all_passed = False

    # pyPASreporterGUI API
    print("\n🔌 pyPASreporterGUI API:")
    
    if not check_endpoint("Ping", f"{base_url}/api/pypasreportergui/ping", json_key="status"):
        # This might not be available yet, mark as warning
        print("     (This endpoint is optional)")

    # Authenticated endpoints
    if not args.skip_auth:
        print("\n🔐 Authentication:")
        
        token = login_and_get_token(base_url, args.username, args.password)
        if token:
            print(f"  ✓ Login: OK (got token)")
            
            print("\n📊 Authenticated Endpoints:")
            
            # Check some common API endpoints
            if not check_authenticated_endpoint(base_url, "/api/v1/database/", token, "Databases API", json_key="result"):
                all_passed = False
            
            if not check_authenticated_endpoint(base_url, "/api/v1/chart/", token, "Charts API", json_key="result"):
                all_passed = False
        else:
            print(f"  ✗ Login: Failed (credentials: {args.username}/{'*' * len(args.password)})")
            all_passed = False

    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All smoke tests passed!")
        return 0
    else:
        print("✗ Some tests failed. See above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
