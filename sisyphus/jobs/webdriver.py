from selenium.webdriver.firefox.service import Service
from seleniumwire import webdriver


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
        self.driver.get(url)
        response = self.get_last_response()
        if response is not None:
            self.last_status_code = response.status_code
        if response is None or response.status_code in [403, 404, 429, 500, 501, 502, 503, 504]:
            return None
        return response

    def quit(self):
        if hasattr(self, 'driver'):
            self.driver.quit()
