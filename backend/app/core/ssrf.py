"""SSRF protection for outbound HTTP calls.

Server-side requests must never be able to reach private, loopback, link-local, or
cloud-metadata endpoints. This guard validates a URL before the platform makes an
outbound request (webhook delivery, connector sync, provider calls).
"""
import asyncio
import ipaddress
import logging
import socket
from urllib.parse import urlparse

logger = logging.getLogger("omniai.ssrf")

# Cloud metadata endpoints that must never be reachable.
_BLOCKED_HOSTNAMES = {
    "169.254.169.254",
    "metadata.google.internal",
    "metadata.googleapis.com",
    "instance-data.ec2.internal",
    "instance-data",
}
_BLOCKED_SUFFIXES = (".internal", ".local", ".localhost")
_BLOCKED_SCHEMES = ("", "file", "ftp", "gopher", "dict", "ldap", "smb")

_BLOCKED_NETWORKS = [
    ipaddress.ip_network(net)
    for net in (
        "0.0.0.0/8",      # this host on this network
        "10.0.0.0/8",     # private
        "100.64.0.0/10",  # carrier-grade NAT
        "127.0.0.0/8",    # loopback
        "169.254.0.0/16", # link-local / cloud metadata
        "172.16.0.0/12",  # private
        "192.0.0.0/24",   # IETF protocol assignments
        "192.168.0.0/16", # private
        "198.18.0.0/15",  # benchmarking
        "224.0.0.0/4",    # multicast
        "240.0.0.0/4",    # reserved
        "::1/128",        # IPv6 loopback
        "fc00::/7",       # IPv6 unique local
        "fe80::/10",      # IPv6 link-local
        "ff00::/8",       # IPv6 multicast
    )
]


class SSRFBlockedError(Exception):
    """Raised when a target URL resolves to a disallowed (non-public) destination."""


def _is_blocked_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return True  # unparseable address -> reject conservatively
    return any(ip in net for net in _BLOCKED_NETWORKS)


def _is_blocked_hostname(hostname: str) -> bool:
    host = hostname.lower().rstrip(".")
    if host in _BLOCKED_HOSTNAMES:
        return True
    if host.startswith("169.254."):
        return True
    for suffix in _BLOCKED_SUFFIXES:
        if host.endswith(suffix):
            return True
    # bare hostnames that are not FQDNs are suspect
    return "." not in host


async def validate_outbound_url(url: str) -> str:
    """Validate that `url` is safe for a server-side request. Returns the URL if safe."""
    parsed = urlparse(url)
    if parsed.scheme in _BLOCKED_SCHEMES:
        raise SSRFBlockedError(f"Blocked scheme '{parsed.scheme}'")
    if parsed.scheme not in ("http", "https"):
        raise SSRFBlockedError(f"Blocked scheme '{parsed.scheme}'")
    if not parsed.hostname:
        raise SSRFBlockedError("Missing hostname")

    hostname = parsed.hostname

    # Literal IP addresses are checked directly.
    try:
        addr = ipaddress.ip_address(hostname)
        if _is_blocked_ip(str(addr)):
            raise SSRFBlockedError(f"Blocked IP address: {hostname}")
        return url
    except ValueError:
        pass  # not a literal IP, treat as hostname

    if _is_blocked_hostname(hostname):
        raise SSRFBlockedError(f"Blocked hostname: {hostname}")

    # Resolve (async-safe) and reject if any address is private/reserved.
    try:
        infos = await asyncio.get_running_loop().getaddrinfo(hostname, None)
    except (socket.gaierror, RuntimeError) as exc:
        raise SSRFBlockedError(f"Could not resolve hostname: {hostname}") from exc

    for info in infos:
        sockaddr = info[4][0]
        if _is_blocked_ip(sockaddr):
            raise SSRFBlockedError(f"Blocked resolved address {sockaddr} for {hostname}")

    return url
