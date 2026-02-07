from django.core.management.base import BaseCommand

from sisyphus.searches.playwright import Scraper


class Command(BaseCommand):
    def handle(self, *args, **options):
        scraper = Scraper()
        print(scraper.scrape('https://icanhazip.com/'))
        print(scraper.scrape('https://icanhazip.com/'))
        scraper.close()
