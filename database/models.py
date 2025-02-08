from datetime import datetime

from peewee import *

from utils import *
from config import *


db = SqliteDatabase("database/SearchOnion.db")
crawl_history_db = SqliteDatabase("database/CrawlHistory.db")
tg_db = SqliteDatabase("database/TG.db")



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
        and not in recent crawl history,
        unless the 'force' flag is set to True.
        
        return True if URL added in queue, else False
        """

        url_hash = hash_sha256(url)

        if cls.get_or_none(cls.url_hash==url_hash):
            return True

        if force:
            cls.create(
                url = url,
                url_hash = url_hash,
            )
            return True

        domain = get_domain(url)
        domain_status = DomainCrawlStatus.get_or_none(DomainCrawlStatus.domain_hash==domain_hash)
        if domain_status.crawl_count >= DOMAIN_MAX_CRAWL_LIMIT:
            return False
        if CrawlHistory.find(url):
            return False

        cls.create(
            url = url,
            url_hash = url_hash,
        )
        return True

    @classmethod
    def peak(cls) -> str:
        """
        Return a top URL to crawl from queue
        """

        if not self.size():
            return ""

        url = cls.select().first()
        if url:
            return url.url

    @classmethod
    def remove(cls, url: str):
        """
        Remove URL from queue, if exists
        """
        url = cls.get_or_none(cls.url_hash==hash_sha256(url))
        if url:
            url.delete_instance()
    
    @classmethod
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
    robots_txt = TextField(default="")

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


class CrawlHistory(crawl_history_db.Model):
    class Meta:
        databese = crawl_history_db

    id = AutoField()
    url = TextField()
    url_hash = FixedCharField(64, index=True)
    crawl_time = DateTimeField(default=datetime.utcnow)
    status_code = IntegerField()
    crawl_status = CharField()
    size_sum = IntegerField()

    @classmethod
    def add(cls, url: str, status_code: int, crawl_status: str, response_size: int):
        """ Add URL to Crawl History """

        url_hash = hash_sha256(url)

        latest = cls.select().order_by(
            cls.id.desc()
        ).first()

        size_sum = response_size
        if latest:
            size_sum = latest.size_sum + response_size
        
        cls.create(
            url = url,
            url_hash = url_hash,
            status_code = status_code,
            crawl_status = crawl_status,
            size_sum = size_sum,
        )

        cls.purge()

    @classmethod
    def find(cls, url: str):
        """Find URL in Crawl History

        Return if found
        """
        return cls.select().order_by(
            cls.id.desc()
        ).first()

    @classmethod
    def purge(cls):
        """ Maintain the history size """
        # presisting the database from getting empty
        if cls.size() <= 1:
            return
        to_be_delete = cls.select().limit(cls.size() - CRAWLED_URL_HISTORY_SIZE)
        for history in to_be_delete:
            to_be_delete.delete_instance()

    @classmethod
    def size(cls) -> int:
        """ Return History Size """
        return cls.select().count()


class DailyReportSubscribers(tg_db.Model):
    class Meta:
        database = tg_db

    id = AutoField()
    tg_id = IntegerField(unique=True)
    first_name = CharField()

    @classmethod
    def subscribe(cls, tg_id: int, name: str = ""):
        """ Subscribe the User to daily reports """
        try:
            cls.create(
                tg_id = tg_id,
                name = name
            )
        except:
            pass
    
    @classmethod
    def unsubscribe(cls, tg_id: int):
        """ Unsubscribe the User from daily Report """
        subscription = cls.get_or_none(cls.tg_id == tg_id)
        if subscription:
            subscription.delete_instance()


db.create_tables([
    CrawlQueue,
    DomainCrawlStatus,
    OnionDomain,
])

crawl_history_db.create_tables([CrawlHistory])

tg_db.create_tables([
    DailyReportSubscribers,
])

