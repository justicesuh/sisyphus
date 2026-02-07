from bs4 import BeautifulSoup

from sisyphus.searches.playwright import Scraper


class BaseParser:
    def __init__(self):
        self.scraper = Scraper()

    def get(self, url: str) -> BeautifulSoup:
        html = self.scraper.get(url)
        return self.soupify(html)

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
