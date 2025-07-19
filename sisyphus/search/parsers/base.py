from django.conf import settings

from sisyphus.search.webdriver import Firefox


class BaseParser:
    def __init__(self):
        self.firefox = Firefox(settings.SEARCH_PROXY, None, None)

    def quit(self):
        self.firefox.quit()


class IPParser(BaseParser):
    def parse(self):
        response = self.firefox.get_with_retry('https://icanhazip.com/')
        if response is not None:
            soup = self.firefox.soupify()
            return soup.find('pre').text.strip()
        return None
