import socket
import ipaddress
from urllib.parse import urlparse, urljoin
import requests
from typing import Optional

class ConnectorSecurityError(Exception):
    """Raised when a URL fails any safety check."""
    pass

class SafeLiveConnector:
    def __init__(self):
        self.max_redirects = 3
        self.max_size_bytes = 1 * 1024 * 1024  # 1 MB limit
        self.connect_timeout = 3.0
        self.read_timeout = 5.0
        self.allowed_content_types = ['text/html', 'application/json', 'text/plain']

    def is_safe_ip(self, hostname: str) -> bool:
        """Resolves hostname to IP and blocks private/internal networks."""
        try:
            ip = socket.gethostbyname(hostname)
            ip_obj = ipaddress.ip_address(ip)
            
            # Restrict private networks (e.g., 127.0.0.1, 192.168.x.x, 10.x.x.x)
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved or ip_obj.is_multicast:
                return False
            return True
        except socket.gaierror:
            return False # DNS resolution failed

    def fetch(self, url: str, redirects_left: Optional[int] = None) -> str:
        """Safely fetches content from a URL."""
        if redirects_left is None:
            redirects_left = self.max_redirects

        if redirects_left < 0:
            raise ConnectorSecurityError("Too many redirects.")

        parsed_url = urlparse(url)
        if parsed_url.scheme not in ('http', 'https'):
            raise ConnectorSecurityError("Only HTTP and HTTPS are supported.")

        if not parsed_url.hostname or not self.is_safe_ip(parsed_url.hostname):
            raise ConnectorSecurityError(f"URL resolves to a restricted private IP or invalid host: {url}")

        try:
            # We set allow_redirects=False so we can manually inspect the redirect URL's IP for safety
            response = requests.get(
                url, 
                stream=True, 
                allow_redirects=False, 
                timeout=(self.connect_timeout, self.read_timeout)
            )
            
            # 1. Safe Redirect Handling
            if response.status_code in (301, 302, 303, 307, 308):
                new_location = response.headers.get('Location')
                if not new_location:
                    raise ConnectorSecurityError("Redirected but missing Location header.")
                
                # Resolve relative redirects (e.g., /new-path) to absolute URLs
                next_url = urljoin(url, new_location)
                return self.fetch(next_url, redirects_left - 1)
                
            response.raise_for_status()

            # 2. Supported Content-Type Checks
            content_type = response.headers.get('Content-Type', '').split(';')[0].lower()
            if content_type and content_type not in self.allowed_content_types:
                raise ConnectorSecurityError(f"Unsupported content type: {content_type}")

            # 3. Response-Size Limits (Memory protection)
            content = b""
            for chunk in response.iter_content(chunk_size=8192):
                content += chunk
                if len(content) > self.max_size_bytes:
                    raise ConnectorSecurityError("Response exceeded the 1MB size limit.")
            
            return content.decode('utf-8', errors='replace')

        except requests.RequestException as e:
            raise ConnectorSecurityError(f"Network request failed: {str(e)}")