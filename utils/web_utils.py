from urllib.parse import urlparse
import re

from requests import get
import tldextract


def get_domain(url: str) -> str:
    """
    Extracts and returns the domain from a given URL
    """
    parsed_url = urlparse(url)
    return parsed_url.netloc

def fetch_html(url: str) -> (str, int):
    """
    Extract and returns HTML of web page and status code
    """
    r = get(url)
    return r.text, r.status_code

def extract_links(html: str) -> list[str]:
    """
    Extract and return links from an HTML
    """
    link_regex = re.compile(r'href=[\'"]?([^\'" >]+)')
    return link_regex.findall(html)

def is_valid_url(url: str) -> bool:
    extracted = tldextract.extract(url)
    return bool(extracted.domain and extracted.suffix)

def remove_protocol(url: str) -> str:
    """
    Removes the protocol from a given URL.
    """
    parsed_url = urlparse(url)
    return parsed_url.netloc + parsed_url.path
