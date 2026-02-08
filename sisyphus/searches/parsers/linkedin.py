from urllib.parse import urlparse

from sisyphus.searches.parsers.base import BaseParser


class LinkedInParser(BaseParser):
    def intercept_request(self, route):
        super().intercept_request(route)
        url = urlparse(route.request.url)
        if url.hostname == 'www.linkedin.com' and url.path.strip('/') in ['', 'authwall', 'favicon.ico']:
            route.abort()
        else:
            route.continue_()
