#!/bin/bash
# Script to fix the http_utils module issue

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Fixing http_utils module issue${NC}"
echo "========================================"

# Create http_utils.py file
cat > payment/http_utils.py << 'EOF'
"""
HTTP utilities for Travian Whispers.
This module provides HTTP request functionality without relying on external dependencies.
"""
import logging
import urllib.request
import urllib.parse
import urllib.error
import json
import ssl
import base64
from typing import Dict, Any, Optional, Tuple, Union

# Configure logger
logger = logging.getLogger(__name__)

def urlencode(params: Dict[str, Any]) -> str:
    """
    URL encode a dictionary of parameters.
    
    Args:
        params: Dictionary of parameters
        
    Returns:
        URL encoded string
    """
    return urllib.parse.urlencode(params)

def basic_auth_header(username: str, password: str) -> Dict[str, str]:
    """
    Create a basic authentication header.
    
    Args:
        username: Username
        password: Password
        
    Returns:
        Dictionary containing the Authorization header
    """
    auth_string = f"{username}:{password}"
    encoded_auth = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
    return {"Authorization": f"Basic {encoded_auth}"}

def perform_request(
    url: str,
    method: str = "GET",
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Union[Dict[str, Any], str]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 30,
    verify_ssl: bool = True
) -> Tuple[int, Dict[str, Any], bytes]:
    """
    Perform an HTTP request using urllib.
    
    Args:
        url: URL to request
        method: HTTP method (GET, POST, etc.)
        params: URL parameters
        data: Request body data
        headers: Request headers
        timeout: Request timeout in seconds
        verify_ssl: Whether to verify SSL certificates
        
    Returns:
        Tuple of (status code, headers, response content)
    """
    # Prepare URL
    if params:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}{urlencode(params)}"
    
    # Prepare headers
    request_headers = headers or {}
    if not any(key.lower() == 'user-agent' for key in request_headers):
        request_headers['User-Agent'] = 'TravianWhispers/1.0'
    
    # Prepare data
    request_data = None
    if data:
        if isinstance(data, dict):
            request_data = json.dumps(data).encode('utf-8')
            if 'Content-Type' not in request_headers:
                request_headers['Content-Type'] = 'application/json'
        elif isinstance(data, str):
            request_data = data.encode('utf-8')
            if 'Content-Type' not in request_headers:
                request_headers['Content-Type'] = 'application/x-www-form-urlencoded'
        else:
            request_data = data
    
    # Create request
    request = urllib.request.Request(
        url,
        data=request_data,
        headers=request_headers,
        method=method
    )
    
    # Configure SSL context
    context = None
    if not verify_ssl:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    
    try:
        # Perform request
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            status_code = response.status
            response_headers = dict(response.getheaders())
            content = response.read()
            return status_code, response_headers, content
    except urllib.error.HTTPError as e:
        logger.error(f"HTTP error: {e.code} - {e.reason}")
        return e.code, dict(e.headers), e.read()
    except urllib.error.URLError as e:
        logger.error(f"URL error: {e.reason}")
        return 0, {}, str(e.reason).encode('utf-8')
    except Exception as e:
        logger.error(f"Request error: {str(e)}")
        return 0, {}, str(e).encode('utf-8')

def get_json(url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Perform a GET request and parse the response as JSON.
    
    Args:
        url: URL to request
        params: URL parameters
        headers: Request headers
        
    Returns:
        Parsed JSON response or empty dict if failed
    """
    status, _, content = perform_request(url, params=params, headers=headers)
    
    if status >= 200 and status < 300:
        try:
            # Try to decode as UTF-8 but fall back to ISO-8859-1 if needed
            try:
                return json.loads(content.decode('utf-8'))
            except UnicodeDecodeError:
                return json.loads(content.decode('iso-8859-1'))
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON response from {url}")
            return {}
    
    logger.error(f"Request to {url} failed with status {status}")
    return {}

def post_json(
    url: str,
    data: Dict[str, Any],
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Perform a POST request with JSON data and parse the response as JSON.
    
    Args:
        url: URL to request
        data: JSON data to send
        params: URL parameters
        headers: Request headers
        
    Returns:
        Parsed JSON response or empty dict if failed
    """
    headers = headers or {}
    headers['Content-Type'] = 'application/json'
    
    status, _, content = perform_request(
        url,
        method="POST",
        params=params,
        data=data,
        headers=headers
    )
    
    if status >= 200 and status < 300:
        try:
            # Try to decode as UTF-8 but fall back to ISO-8859-1 if needed
            try:
                return json.loads(content.decode('utf-8'))
            except UnicodeDecodeError:
                return json.loads(content.decode('iso-8859-1'))
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON response from {url}")
            return {}
    
    logger.error(f"POST request to {url} failed with status {status}")
    return {}
EOF

# Create a root level module too (in case it needs to be imported from elsewhere)
cat > http_utils.py << 'EOF'
"""
HTTP utilities for Travian Whispers.
This module provides HTTP request functionality without relying on external dependencies.
"""
import logging
import urllib.request
import urllib.parse
import urllib.error
import json
import ssl
import base64
from typing import Dict, Any, Optional, Tuple, Union

# Configure logger
logger = logging.getLogger(__name__)

def urlencode(params: Dict[str, Any]) -> str:
    """
    URL encode a dictionary of parameters.
    
    Args:
        params: Dictionary of parameters
        
    Returns:
        URL encoded string
    """
    return urllib.parse.urlencode(params)

def basic_auth_header(username: str, password: str) -> Dict[str, str]:
    """
    Create a basic authentication header.
    
    Args:
        username: Username
        password: Password
        
    Returns:
        Dictionary containing the Authorization header
    """
    auth_string = f"{username}:{password}"
    encoded_auth = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
    return {"Authorization": f"Basic {encoded_auth}"}

def perform_request(
    url: str,
    method: str = "GET",
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Union[Dict[str, Any], str]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 30,
    verify_ssl: bool = True
) -> Tuple[int, Dict[str, Any], bytes]:
    """
    Perform an HTTP request using urllib.
    
    Args:
        url: URL to request
        method: HTTP method (GET, POST, etc.)
        params: URL parameters
        data: Request body data
        headers: Request headers
        timeout: Request timeout in seconds
        verify_ssl: Whether to verify SSL certificates
        
    Returns:
        Tuple of (status code, headers, response content)
    """
    # Prepare URL
    if params:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}{urlencode(params)}"
    
    # Prepare headers
    request_headers = headers or {}
    if not any(key.lower() == 'user-agent' for key in request_headers):
        request_headers['User-Agent'] = 'TravianWhispers/1.0'
    
    # Prepare data
    request_data = None
    if data:
        if isinstance(data, dict):
            request_data = json.dumps(data).encode('utf-8')
            if 'Content-Type' not in request_headers:
                request_headers['Content-Type'] = 'application/json'
        elif isinstance(data, str):
            request_data = data.encode('utf-8')
            if 'Content-Type' not in request_headers:
                request_headers['Content-Type'] = 'application/x-www-form-urlencoded'
        else:
            request_data = data
    
    # Create request
    request = urllib.request.Request(
        url,
        data=request_data,
        headers=request_headers,
        method=method
    )
    
    # Configure SSL context
    context = None
    if not verify_ssl:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    
    try:
        # Perform request
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            status_code = response.status
            response_headers = dict(response.getheaders())
            content = response.read()
            return status_code, response_headers, content
    except urllib.error.HTTPError as e:
        logger.error(f"HTTP error: {e.code} - {e.reason}")
        return e.code, dict(e.headers), e.read()
    except urllib.error.URLError as e:
        logger.error(f"URL error: {e.reason}")
        return 0, {}, str(e.reason).encode('utf-8')
    except Exception as e:
        logger.error(f"Request error: {str(e)}")
        return 0, {}, str(e).encode('utf-8')

def get_json(url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Perform a GET request and parse the response as JSON.
    
    Args:
        url: URL to request
        params: URL parameters
        headers: Request headers
        
    Returns:
        Parsed JSON response or empty dict if failed
    """
    status, _, content = perform_request(url, params=params, headers=headers)
    
    if status >= 200 and status < 300:
        try:
            # Try to decode as UTF-8 but fall back to ISO-8859-1 if needed
            try:
                return json.loads(content.decode('utf-8'))
            except UnicodeDecodeError:
                return json.loads(content.decode('iso-8859-1'))
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON response from {url}")
            return {}
    
    logger.error(f"Request to {url} failed with status {status}")
    return {}

def post_json(
    url: str,
    data: Dict[str, Any],
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Perform a POST request with JSON data and parse the response as JSON.
    
    Args:
        url: URL to request
        data: JSON data to send
        params: URL parameters
        headers: Request headers
        
    Returns:
        Parsed JSON response or empty dict if failed
    """
    headers = headers or {}
    headers['Content-Type'] = 'application/json'
    
    status, _, content = perform_request(
        url,
        method="POST",
        params=params,
        data=data,
        headers=headers
    )
    
    if status >= 200 and status < 300:
        try:
            # Try to decode as UTF-8 but fall back to ISO-8859-1 if needed
            try:
                return json.loads(content.decode('utf-8'))
            except UnicodeDecodeError:
                return json.loads(content.decode('iso-8859-1'))
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON response from {url}")
            return {}
    
    logger.error(f"POST request to {url} failed with status {status}")
    return {}
EOF

# Also create the necessary empty __init__.py files
touch payment/__init__.py

echo -e "${GREEN}http_utils.py module created successfully${NC}"
echo -e "${YELLOW}Now, restart your Docker containers:${NC}"
echo "docker-compose down"
echo "docker-compose up -d"

echo -e "${GREEN}Done!${NC}"
