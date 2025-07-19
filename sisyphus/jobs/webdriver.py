import logging
import time

from bs4 import BeautifulSoup
from selenium.webdriver.firefox.service import Service
from seleniumwire import webdriver


logging.getLogger('seleniumwire').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


class Firefox:
    def __init__(self):
        self.options = webdriver.FirefoxOptions()
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--headless')

        self.service = Service(executable_path='/usr/local/bin/geckodriver')

        self.seleniumwire_options = None

        self.create_driver()

        self.last_status_code = None

    def create_driver(self):
        self.quit()
        self.driver = webdriver.Firefox(
            options=self.options,
            service=self.service,
            seleniumwire_options=self.seleniumwire_options
        )

    def get_last_response(self):
        request = self.driver.requests[-1] if self.driver.requests else None
        if request is not None:
            return request.response
        return None

    def get(self, url):
        logger.info(f'GET {url}')
        self.driver.get(url)
        response = self.get_last_response()
        if response is not None:
            self.last_status_code = response.status_code
        if response is None or response.status_code in [403, 404, 429, 500, 501, 502, 503, 504]:
            return None
        return response

    def get_with_retry(self, url, retries=8, backoff_factor=1):
        for i in range(retries):
            try:
                response = self.get(url)
                if response is not None:
                    return response
                self.create_driver()
            except Exception:
                self.create_driver()
            backoff = backoff_factor * (2 ** i)
            logger.info(f'Sleeping for {backoff} seconds.')
            time.sleep(backoff)
        logger.info(f'Max retries for {url} exceeded.')
        return None

    def soupify(self):
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        return soup

    def quit(self):
        if hasattr(self, 'driver'):
            self.driver.quit()
