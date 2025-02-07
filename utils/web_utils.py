from urllib.parse import urlparse
from requests import get


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

def get_links(html: str) -> list[str]:
    """
    Extract and return links from an HTML
    """
    NotImplementedError
