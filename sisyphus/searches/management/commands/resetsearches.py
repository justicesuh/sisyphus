from django.core.management.base import BaseCommand

from sisyphus.searches.models import Search, SearchRun


class Command(BaseCommand):
    def handle(self, **options):
        for run in SearchRun.objects.all():
            if run.status == SearchRun.Status.RUNNING:
                run.delete()
        for search in Search.objects.all():
            if search.status == Search.Status.RUNNING:
                search.set_status(Search.Status.IDLE)
