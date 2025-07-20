import itertools

from django.core.management.base import BaseCommand

from sisyphus.jobs.models import Location, Job
from sisyphus.search.models import Search


class Command(BaseCommand):
    help = 'Generate search combinations based on keywords'

    def handle(self, **options):
        search_terms = [
            'python',
            'django',
            'flask',
            'fastapi',
            'founding engineer python',
            'technical cofounder python',
        ]
        combinations = list(itertools.product(list(dict(Search.PERIOD_CHOICES).keys()), [True, False]))
        count = 0

        us, _ = Location.objects.get_or_create(geo_id=103644278, defaults={'name': 'United States'})
        for keywords in search_terms:
            for period, easy_apply in combinations:
                _, created = Search.objects.get_or_create(
                    keywords=keywords,
                    location=us,
                    easy_apply=easy_apply,
                    flexibility=Job.REMOTE,
                    period=period,
                )
                if created:
                    count += 1

        self.stdout.write(self.style.SUCCESS(f'Created {count} searches.'))
