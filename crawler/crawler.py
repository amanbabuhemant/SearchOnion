from time import sleep
from xml.etree import ElementTree

from database import *
from utils import *
from config import *

from .logger import logger


class Crawler:
    """Crawler"""

    def __init__(self):
        self.crawl_delay = DEFAULT_CRAWL_DELAY
        self._stop = True

    def crawl(self, url: str):
        """ Crawl an URL """
        
        if not is_valid_url(url):
            logger.info(f"Invalid URL {url}, skpping crawl")
            CrawlQueue.remove(url)
            return

        url = remove_protocol(url).strip()
        domain = get_domain(url)
        domain_hash = hash_sha256(domain)
        if url == domain:
            url += "/"

        crawl_history = CrawlHistory.find(url)
        if crawl_history:
            logger.info(f"URL found in crawl history, skipping")
            CrawlQueue.remove(url)
            return

        if domain.endswith(".onion"):
            # skipping because tor fetcher isn't implimented
            logger.info(f"An .onion link encounterd, skipping crawl")
            onion_domain: OnionDomain = OnionDomain.find(domain)
            if not onion_domain:
                onion_domain = OnionDomain.create(
                    domain = domain,
                    domain_hash = domain_hash
                )
            CrawlQueue.remove(url)
            CrawlHistory.add(url, 0, "Can't fetch tor network currently", 0)
            return

        domain_crawl_status: DomainCrawlStatus = DomainCrawlStatus.get_status(domain)
        if not domain_crawl_status:
            logger.info(f"New domain {domain} fonud")
            robots_txt = fetch_url(domain + "/robots.txt")

            domain_crawl_status = DomainCrawlStatus.create(
                domain = domain,
                domain_hash = domain_hash,
                robots_txt = robots_txt
            )

            for key, value in domain_crawl_status.robots_txt_list():
                if key == "Sitemap":
                    if value.startswith("/"):
                        value = domain + value
                    sitemap = fetch_url(value)
                    if sitemap:
                        if value.lower().endswith(".xml"):
                            self.parse_and_queue_xml_sitemap(sitemap)
                        if value.lower().endswith(".txt"):
                            self.parse_and_queue_txt_sitemap(sitemap)

        if not self.is_allowed_to_crawl(url):
            logger.info(f"Not allow to fetch {url}")
            CrawlQueue.remove(url)
            CrawlHistory.create(url, 0, "Not allowed by robots.txt", 0)
            return

        content, return_code = fetch_url(url)
        if not return_code:
            logger.info(f"Can't fetch url {url}")
            CrawlQueue.remove(url)
            CrawlHistory.add(url, 0, "Unable to fetch", 0)
            return

        links = extract_links(content)
        valid_links = 0
        for link in links:
            if link.startswith("/"):
                link = domain + link
            elif not link.startswith("http://") and not link.startswith("https://"):
                url_splits = url.split("/")
                url_splits.pop()
                url_splits.append(link)
                link = "/".join(url_splits)

            if is_valid_url(link):
                valid_links += 1
                CrawlQueue.add(link)
        
        CrawlQueue.remove(url)
        CrawlHistory.add(
            url, return_code,
            "Crawled", len(content)
        )

        DomainCrawlStatus.update_domain_status(domain)
        logger.info(f"Crawling completed for {url}, {valid_links} links found")

    def is_allowed_to_crawl(self, url) -> bool:
        """
        Check if the spasfic URL is allowed to crawl by the Crawler or not
        this consider the Domain's robots.txt

        currently don't suport * and $ notation
        """
        # TODO: support for * and $

        url = remove_protocol(url)
        domain = get_domain(url)
        if domain == url:
            url += "/"
        path = url[len(domain):]

        domain_status: DomainCrawlStatus = DomainCrawlStatus.get_status(domain)
        if not domain_status:
            return None
        us = False
        allow = True
        for key, value in domain_status.robots_txt_list():
            if key == "User-agent" and value == "*":
                us = True
            if key == "User-agent" and value != "*":
                us = False
            if us:
                if key == "Allow":
                    if path.startswith(value):
                        allow = True
                if key == "Disallow":
                    if path.startswith(value):
                        allow = False
        return allow

    def parse_and_queue_xml_sitemap(sitemap: str):
        """
        Parse the XML sitemap and extract likns and add in Crawl Queue
        Will not exceed the crawl limit configerd for domains
        """
        DOMAIN_MAX_CRAWL_LIMIT
        added = 0
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        root = ElementTree.fromstring(sitemap)
        for loc in root.findall(".//s:loc", ns):
            url = loc.text.strip()
            if is_valid_url(url):
                CrawlQueue.add(remove_protocol(url))
                added += 1
            if added == DOMAIN_MAX_CRAWL_LIMIT:
                break
    
    def parse_and_queue_txt_sitemap(sitemap: str):
        """
        Parse the TXT sitemap and extract likns for adding in Crawl Queue
        Will not exceed the crawl limit configerd for domains
        """
        added = 0
        urls = sitemap.split("\n")
        for url in urls:
            url = url.strip()
            if is_valid_url(url):
                CrawlQueue.add(url)
                added += 1
            if added == DOMAIN_MAX_CRAWL_LIMIT:
                break
 
    def run(self):
        if self._stop:
            logger.info("Crawler started")
        self._stop = False
        while not self._stop:
            url = CrawlQueue.peak()
            if not url:
                logger.warning("No URL found, Crawl Queue is empty")
                sleep(60)
                continue
            try:
                self.crawl(url)
            except KeyboardInterrupt:
                logger.info("Keyborad Interrupt detected, stoppnig Crawler")
                self._stop = True
                print("KeyboardInterrupt")
                print("Try again if programm crawler didn't stop")
                sleep(5)
            except Exception as e:
                logger.warn(str(e))
                sleep(10)
        logger.info("Crawler stopped")

    def stop(self):
        self._stop = True
        logger.info("Stopping Crawler")
