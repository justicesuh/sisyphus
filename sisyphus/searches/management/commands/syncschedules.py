from django.core.management.base import BaseCommand

from sisyphus.searches.models import Search


class Command(BaseCommand):
    help = 'Sync celery beat schedules for all searches'

    def handle(self, *args, **options):
        searches = Search.objects.all()
        for search in searches:
            search.sync_schedule()
            self.stdout.write(f'{search.keywords}: {"synced" if search.schedule and search.is_active else "cleared"}')
        self.stdout.write(self.style.SUCCESS(f'Synced {searches.count()} searches'))
