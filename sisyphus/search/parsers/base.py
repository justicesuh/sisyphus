import logging

from django.conf import settings

from sisyphus.search.webdriver import Firefox


logger = logging.getLogger(__name__)


firefox_blocklist = [
    'detectportal.firefox.com',
    'firefox.settings.services.mozilla.com',
    'shavar.services.mozilla.com',
    'content-signature-2.cdn.mozilla.net',
    'tracking-protection.cdn.mozilla.net',
]


class BaseParser:
    blocklist = []

    def __init__(self, log_intercepts=False):
        self.log_intercepts = log_intercepts
        self.firefox = Firefox(settings.SEARCH_PROXY, self.intercept_request, self.process_response)

    def intercept_request(self, request):
        if request.host in firefox_blocklist + self.blocklist:
            request.abort(error_code=404)
        elif self.log_intercepts:
            logger.info(f'Intercepting {request.host}')

    def process_response(self, requests):
        if requests is None:
            return None
        for request in reversed(requests):
            response = request.response
            if request.response is None or request.response.status_code == 404:
                return None
            return response

    def quit(self):
        self.firefox.quit()


class IPParser(BaseParser):
    def parse(self):
        response = self.firefox.get_with_retry('https://icanhazip.com/')
        if response is not None:
            soup = self.firefox.soupify()
            return soup.find('pre').text.strip()
        return None
