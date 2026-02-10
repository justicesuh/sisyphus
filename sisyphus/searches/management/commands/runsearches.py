from django.core.management.base import BaseCommand

from sisyphus.searches.models import Search
from sisyphus.searches.tasks import execute_search


class Command(BaseCommand):
    help = 'Queue execute_search for all active searches'

    def handle(self, *args, **options):
        searches = Search.objects.filter(is_active=True)
        for search in searches:
            execute_search.delay(search.id, search.user_id)
            self.stdout.write(f'Queued: {search.keywords}')
        self.stdout.write(self.style.SUCCESS(f'Queued {searches.count()} searches'))
