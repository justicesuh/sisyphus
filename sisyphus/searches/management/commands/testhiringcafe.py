import json

from django.core.management.base import BaseCommand

from sisyphus.searches.parsers.hiringcafe import HiringCafeParser


class Command(BaseCommand):
    def handle(self, **options):
        parser = HiringCafeParser()
        data = parser.parse('django')
        print(data)