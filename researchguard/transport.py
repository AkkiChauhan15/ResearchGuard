"""Restricted HTTPS transport; DNS is checked once and the connection pins that IP."""
import http.client
import ipaddress
import socket
import ssl
import time
from urllib.parse import urljoin, urlsplit

MAX_BYTES = 2_000_000
HOSTS = {'eutils.ncbi.nlm.nih.gov', 'pubmed.ncbi.nlm.nih.gov',
         'pmc.ncbi.nlm.nih.gov', 'www.enzo.com'}


class FetchError(ValueError):
    def __init__(self, message, state='fetch_failed'):
        super().__init__(message)
        self.state = state


def validate_url(url):
    if not isinstance(url, str) or len(url) > 3000 or any(ord(c) < 33 for c in url):
        raise FetchError('Invalid URL.')
    try:
        p = urlsplit(url)
        if p.scheme != 'https' or p.hostname not in HOSTS or p.port not in (None, 443) or p.username or p.password or p.fragment:
            raise ValueError()
    except ValueError:
        raise FetchError('Only supported public HTTPS destinations are allowed.') from None
    return p


def public_address(host):
    try:
        addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except OSError:
        raise FetchError('Public source DNS lookup failed.') from None
    if not addresses:
        raise FetchError('No public address resolved.')
    for _, _, _, _, addr in addresses:
        ip = ipaddress.ip_address(addr[0])
        if not ip.is_global or (getattr(ip, 'ipv4_mapped', None) and not ip.ipv4_mapped.is_global):
            raise FetchError('A destination resolved to a non-public network; request blocked.')
    return addresses[0][4][0]


class PinnedHTTPS(http.client.HTTPSConnection):
    def __init__(self, hostname, address, timeout):
        super().__init__(hostname, timeout=timeout, context=ssl.create_default_context())
        self.address = address

    def connect(self):
        raw = socket.create_connection((self.address, 443), timeout=self.timeout)
        try:
            self.sock = self._context.wrap_socket(raw, server_hostname=self.host)
        except Exception:
            raw.close()
            raise


def fetch(url, *, body=None, headers=None, timeout=15, allowed_types=None):
    """No proxy inheritance, automatic redirects, cookies, or credential forwarding."""
    deadline = time.monotonic() + timeout
    allowed_types = allowed_types or {'application/xml', 'text/xml', 'text/html', 'application/json'}
    for _ in range(4):
        p = validate_url(url)
        address = public_address(p.hostname)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise FetchError('Source request timed out.')
        conn = PinnedHTTPS(p.hostname, address, min(remaining, 15))
        try:
            req_headers = {'User-Agent': 'ResearchGuardAI/0.1 (local research preview)', 'Accept-Encoding': 'identity'}
            req_headers.update(headers or {})
            conn.request('POST' if body is not None else 'GET', p.path + ('?' + p.query if p.query else ''), body=body, headers=req_headers)
            if conn.sock:
                conn.sock.settimeout(max(.01, deadline - time.monotonic()))
            res = conn.getresponse()
            if res.status in (301, 302, 303, 307, 308):
                if body is not None or headers:
                    raise FetchError('Redirect on credentialed request blocked.')
                location = res.getheader('Location')
                if not location:
                    raise FetchError('Redirect has no destination.')
                url = urljoin(url, location)
                validate_url(url)
                continue
            if res.status == 429:
                raise FetchError('Source rate limit reached; retry later.', 'rate_limited')
            if res.status != 200:
                raise FetchError(f'Source returned HTTP {res.status}.')
            content_type = res.getheader('Content-Type', '').split(';')[0].lower().strip()
            if content_type not in allowed_types or res.getheader('Content-Encoding', 'identity') != 'identity':
                raise FetchError('Unsupported source content type or encoding.', 'parse_failed')
            length = res.getheader('Content-Length')
            if length and int(length) > MAX_BYTES:
                raise FetchError('Source exceeds the 2 MB retrieval limit.', 'partial_access')
            chunks, count = [], 0
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise FetchError('Source request timed out.')
                if conn.sock:
                    conn.sock.settimeout(remaining)
                chunk = res.read1(min(65536, MAX_BYTES + 1 - count))
                count += len(chunk)
                if count > MAX_BYTES:
                    raise FetchError('Source exceeds the 2 MB retrieval limit.', 'partial_access')
                if not chunk:
                    break
                chunks.append(chunk)
            return b''.join(chunks), url, dict(res.getheaders())
        except FetchError:
            raise
        except (TimeoutError, socket.timeout):
            raise FetchError('Source request timed out.') from None
        except (OSError, ValueError, http.client.HTTPException):
            raise FetchError('Public source connection or response failed.') from None
        finally:
            conn.close()
    raise FetchError('Too many redirects.')
