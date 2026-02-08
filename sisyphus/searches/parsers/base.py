import logging
from typing import ClassVar
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from sisyphus.searches.playwright import Scraper

logger = logging.getLogger(__name__)


class BaseParser:
    blocklist: ClassVar[list[str]] = []

    def __init__(self):
        self.scraper = Scraper(self.intercept_request)

    def intercept_request(self, route) -> bool:
        host = urlparse(route.request.url).hostname
        if host in self.blocklist:
            route.abort()
        else:
            logger.info('Intercepting %s', host)
            if type(self).intercept_request is BaseParser.intercept_request:
                route.continue_()

    def get(self, url: str) -> BeautifulSoup:
        if (html := self.scraper.get_with_retry(url, max_retries=2)) is not None:
            return self.soupify(html)
        return self.soupify('')

    def soupify(self, html: str) -> BeautifulSoup:
        return BeautifulSoup(html, 'html.parser')
    
    def close(self):
        self.scraper.close()


class IPParser(BaseParser):
    def parse(self) -> str:
        soup = self.get('https://icanhazip.com/')
        if (tag := soup.find('pre')) is not None:
            return tag.text.strip()
        return ''
