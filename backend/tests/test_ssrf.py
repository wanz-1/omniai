"""Tests for the SSRF guard (app/core/ssrf.py)."""
import pytest

from app.core.ssrf import SSRFBlockedError, validate_outbound_url


@pytest.mark.asyncio
async def test_allows_public_https_url():
    assert await validate_outbound_url("https://example.com") == "https://example.com"
    assert await validate_outbound_url("https://api.github.com/user") == "https://api.github.com/user"


@pytest.mark.asyncio
async def test_blocks_private_literal_ip():
    for ip in ("http://127.0.0.1:8080/admin", "http://10.0.0.5", "http://192.168.1.1", "http://172.16.0.1"):
        with pytest.raises(SSRFBlockedError):
            await validate_outbound_url(ip)


@pytest.mark.asyncio
async def test_blocks_cloud_metadata():
    for url in (
        "http://169.254.169.254/latest/meta-data/",
        "http://metadata.google.internal/computeMetadata/v1/",
        "http://metadata.googleapis.com/",
    ):
        with pytest.raises(SSRFBlockedError):
            await validate_outbound_url(url)


@pytest.mark.asyncio
async def test_blocks_localhost_and_internal_hostnames():
    for url in ("http://localhost:5432", "http://myhost.local", "http://db.internal:3306"):
        with pytest.raises(SSRFBlockedError):
            await validate_outbound_url(url)


@pytest.mark.asyncio
async def test_blocks_non_http_schemes():
    for url in ("file:///etc/passwd", "ftp://example.com", "gopher://example.com:70/1", "ldap://example.com"):
        with pytest.raises(SSRFBlockedError):
            await validate_outbound_url(url)


@pytest.mark.asyncio
async def test_blocks_missing_hostname():
    with pytest.raises(SSRFBlockedError):
        await validate_outbound_url("https://")


@pytest.mark.asyncio
async def test_blocks_link_local_ipv6():
    with pytest.raises(SSRFBlockedError):
        await validate_outbound_url("http://[fe80::1]:8080/")
