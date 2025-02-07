from datetime import datetime

from peewee import *

from utils import *


db = SqliteDatabase("OnionSearch.db")


class BaseModel(db.Model):
    class Meta:
        database = db


class CrawlQueue(BaseModel):
    """Crawl Queue

    URL's Queue for crawiling URL by the crawler
    """

    id = AutoField()
    url = TextField(unique=True)
    url_hash = FixedCharField(64, index=True)

    @classmethod
    def add(cls, url: str, force: bool = False) -> bool:
        """
        Adds a URL to the queue if the domain has not reached the crawl limit,  
        unless the 'force' flag is set to True.
        
        return True if URL added in queue, else False
        """

        url_hash = hash_sha256(url)

        if not force:
            if cls.get_or_none(cls.url_hash==url_hash):
                return False

    @classmethod
    def get(cls) -> str:
        """
        Return a URL to crawl from queue
        """

        if not self.size:
            return ""

        url = cls.select().limit(1)[0]
        return url.url

    @classmethod
    def remove(cls, url: str):
        """
        Remove URL from queue, if exists
        """
        url = cls.get_or_none(cls.url_hash==hash_sha256(url))
        if url:
            url.delete_instance()
    
    @property
    def size(cls) -> int:
        """
        Return Queue size
        """
        return cls.select().count()


class DomainCrawlStatus(BaseModel):
    """Crawl Status

    Crawl status of domain,
    """

    id = AutoField()
    domain = TextField()
    domain_hash = FixedCharField(64, index=True)
    crawl_count = IntegerField(default=0)
    last_crawl = DateTimeField(default=datetime.utcnow)

    @classmethod
    def update_domain_status(cls, domain: str, crawl: int = 1):
        if crawl < 1:
            return

        domain_hash = hash_sha256(domain) 

        status = cls.get_or_none(cls.domain_hash==domain_hash)
        if not status:
            status = cls.create(
                damain = domain,
                domain_hash = domain_hash,
            )

        status.crawl_count += crawl
        status.last_crawl = datetime.utcnow()
        status.save()


class OnionDomain(BaseModel):
    """Onion domains"""

    id = AutoField()
    domain = TextField()
    domain_hash = FixedCharField(64, index=True)
    first_found = DateTimeField(datetime.utcnow)
    working = BooleanField(null=True, default=None)
    last_check = DateTimeField(null=True, default=None)

    @classmethod
    def update_domain_status(cls, domain: str, worknig: bool = None):
        """
        Updates domain status
        """
        if domain := cls.get_or_none(cls.domain_hash==hash_sha256(domain)):
            domain.working = working
            domain.last_ceck = datetime.utcnow()
            domain.save()


db.create_tables([
    CrawlQueue,
    DomainCrawlStatus,
    OnionDomain,
])    
