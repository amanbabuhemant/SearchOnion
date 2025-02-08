# cnofigrations

DOMAIN_MAX_CRAWL_LIMIT = 1024
CRAWLED_URL_HISTORY_SIZE = 1_000_000
DEFAULT_CRAWL_DELAY = 2




# production configration
try:
    from prod_config import *
except ImportError:
    pass

# development configration
try:
    from dev_config import *
except ImportError:
    pass

# test configration
try:
    from test_config import *
except ImportError:
    pass
