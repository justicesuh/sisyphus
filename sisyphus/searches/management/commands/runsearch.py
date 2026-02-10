from django.core.management.base import BaseCommand

from sisyphus.searches.models import Search
from sisyphus.searches.tasks import execute_search


class Command(BaseCommand):
    def handle(self, *args, **options):
        search = Search.objects.filter(is_active=True).first()
        execute_search.delay(search.id, search.user_id)
        self.stdout.write(f'Queued: {search.keywords}')
