from django.core.management.base import BaseCommand

from sisyphus.jobs.models import Job
from sisyphus.search.models import Search
from sisyphus.search.parsers.linkedin import LinkedInParser


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--enforce-limit', action='store_true')

    def handle(self, **options):
        parser = LinkedInParser()

        searches = Search.objects.stale().order_by('-period')
        print(f'Found {len(searches)} searches.')
        for search in searches:
            print(f'Executing {search}.')
            page_count = parser.get_page_count(search)
            print(f'Found {page_count} pages.')
            for i in range(page_count):
                page = i + 1
                print(f'Parsing page {page}')
                jobs = parser.parse(search, page)
                count = Job.objects.add_jobs(jobs, search)
                print(f'Added {count} jobs')
            search.update_last_executed()
