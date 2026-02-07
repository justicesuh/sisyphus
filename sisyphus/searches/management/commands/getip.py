from django.core.management.base import BaseCommand

from sisyphus.searches.playwright import Scraper


class Command(BaseCommand):
    help = ''

    def handle(self, *args, **options):
        scraper = Scraper()
        html = scraper.scrape('https://icanhazip.com/')
        print(html)
        scraper.close()
