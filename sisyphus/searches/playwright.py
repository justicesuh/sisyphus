from __future__ import annotations

import logging
from urllib.parse import urlparse

from django.conf import settings
from playwright.sync_api import Browser, Playwright, sync_playwright

logger = logging.getLogger(__name__)


class Scraper:
    """A web scraper that maintains a reusable Playwright browser instance."""

    def __init__(self) -> None:
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None

    @property
    def browser(self) -> Browser:
        """Return the browser instance, launching one if needed."""
        if self._browser is None or not self._browser.is_connected():
            self._ensure_playwright()
            assert self._playwright is not None
            logger.info('Launching browser')
            launch_kwargs: dict[str, object] = {'headless': True}
            proxy = getattr(settings, 'PROXY', None)
            if proxy:
                parsed = urlparse(proxy)
                proxy_config: dict[str, str] = {
                    'server': f'{parsed.scheme}://{parsed.hostname}:{parsed.port}',
                }
                if parsed.username:
                    proxy_config['username'] = parsed.username
                if parsed.password:
                    proxy_config['password'] = parsed.password
                launch_kwargs['proxy'] = proxy_config
            self._browser = self._playwright.chromium.launch(**launch_kwargs)
        return self._browser

    def restart_browser(self) -> None:
        """Close and relaunch the browser to rotate the proxy IP."""
        if self._browser is not None:
            logger.info('Restarting browser for proxy rotation')
            self._browser.close()
            self._browser = None
        # Access the property to trigger a fresh launch.
        _ = self.browser

    def _ensure_playwright(self) -> None:
        """Start the Playwright instance if not already running."""
        if self._playwright is None:
            self._playwright = sync_playwright().start()

    def get(self, url: str, *, wait_until: str = 'networkidle') -> str:
        context = self.browser.new_context()
        try:
            page = context.new_page()
            logger.info('Get %s', url)
            page.goto(url, wait_until=wait_until)
            return page.content()
        finally:
            context.close()

    def close(self) -> None:
        """Shut down the browser and Playwright instances."""
        if self._browser is not None:
            logger.info('Closing browser')
            self._browser.close()
            self._browser = None
        if self._playwright is not None:
            self._playwright.stop()
            self._playwright = None

    def __enter__(self) -> Scraper:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
