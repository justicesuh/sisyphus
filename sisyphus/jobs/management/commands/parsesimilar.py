import logging

from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.utils import timezone

from sisyphus.jobs.models import Job
from sisyphus.searches.utils import NullableTag, remove_query

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--save', action='store_true')

    def parse_job(self, div: NullableTag) -> dict | None:
        """Parse similar job div."""
        error: str | None = None
        job = {}

        try:
            company_link = div.find('h4', {'class': 'base-main-card__subtitle'}).find('a')
            job['company'] = company_link.text
            url = company_link.get('href')
            job['company_url'] = remove_query(url)
        except Exception:
            logger.exception('Error parsing company information')
            error = 'company'

        try:
            job['title'] = div.find('h3', {'class': 'base-main-card__title'}).text
        except Exception:
            logger.exception('Error parsing job title')
            error = 'title'

        try:
            url = div.find('a', {'class': 'base-card__full-link'}).get('href')
            job['url'] = remove_query(url)
        except Exception:
            logger.exception('Error parsing job url')
            error = 'url'

        try:
            job['location'] = div.find('span', {'class': 'main-job-card__location'}).text
        except Exception:
            logger.exception('Unable to get location. Setting to None')
            job['location'] = None

        try:
            time = div.find('time', {'class': 'main-job-card__listdate'}) or div.find(
                'time', {'class': 'main-job-card__listdate--new'}
            )
            job['date_posted'] = time.get('datetime')
        except Exception:
            logger.exception('Error parsing job post date')
            error = 'date_posted'

        job['date_found'] = str(timezone.now())

        if error is not None:
            return None
        return job

    def parse_similar_jobs(self, job: Job) -> list[dict]:
        soup = BeautifulSoup(job.raw_html[len('NullableTag') + 1:-1], 'html.parser')
        try:
            divs = [
                li.find('div', {'class': 'base-main-card'})
                for li in soup.find('section', {'class': 'similar-jobs'}).find('ul').find_all('li')
            ]
        except Exception:
            divs = []
        jobs: list[dict] = []
        for div in divs:
            job = self.parse_job(NullableTag(div))
            if job is not None:
                jobs.append(job)
        return jobs

    def print(self, msg: str):
        logger.info(msg)
        self.stdout.write(msg)

    def handle(self, **options):
        similar_jobs: list[dict] = []
        jobs = Job.objects.filter(status=Job.Status.APPLIED, similar_jobs_parsed=False).exclude(raw_html='')
        self.print(f'Found {len(jobs)} jobs.')
        for job in jobs:
            similar_jobs.extend(self.parse_similar_jobs(job))
        self.print(f'Found {len(similar_jobs)} similar jobs.')

        if options['save']:
            for job in jobs:
                job.similar_jobs_parsed = True
                job.save(update_fields=['similar_jobs_parsed'])
            Job.objects.add_jobs(similar_jobs, None)
