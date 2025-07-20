from django.core.management.base import BaseCommand

from sisyphus.search.models import Search


class Command(BaseCommand):
    def handle(self, **options):
        searches = Search.objects.all()
        for search in searches:
            search.last_executed = None
            search.save()
