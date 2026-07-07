import socket
from urllib.parse import urlparse
import ipaddress

def is_safe_url(url: str) -> bool:
    """
    Checks if a URL is safe to scrape by resolving its hostname
    and ensuring it does not point to a private, loopback, or reserved IP address.
    This prevents Server-Side Request Forgery (SSRF) attacks.
    """
    try:
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname
        if not hostname:
            return False

        # Resolve hostname to IP address
        ip_addr = socket.gethostbyname(hostname)
        ip = ipaddress.ip_address(ip_addr)

        # Block private, loopback, multicast, and other reserved IPs
        if ip.is_private or ip.is_loopback or ip.is_multicast or ip.is_reserved:
            return False
            
        return True
    except Exception as e:
        print(f"URL Safety check failed for {url}: {e}")
        return False
