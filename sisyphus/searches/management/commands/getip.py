from django.core.management.base import BaseCommand

from sisyphus.searches.parsers.base import IPParser


class Command(BaseCommand):
    def handle(self, *args, **options):
        parser = IPParser()
        print(parser.parse())
        print(parser.parse())
        parser.close()
