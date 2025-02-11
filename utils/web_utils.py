from urllib.parse import urlparse
import re

from requests import get
import tldextract


def get_domain(url: str) -> str:
    """
    Extracts and returns the domain from a given URL
    """
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "http://" + url
    parsed_url = urlparse(url)
    return parsed_url.netloc

def fetch_url(url: str) -> (str, int):
    """
    Extract and returns HTML of web page and status code
    """
    if not url.startswith("http://") or not url.startswith("https://"):
        url = "https://" + remove_protocol(url)
    try:
        r = get(url)
        return r.text, r.status_code
    except:
        try:
            url = "http://" + remove_protocol(url)
            r = get(url)
            return r.text, r.status_code
        except:
            """ cannot fetch the url """
    return "", 0

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
